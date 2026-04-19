import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routers import admin, auth, borrowings, equipments, labs, maintenance, notifications, penalties, reports, reservations, staff, users
from app.config import get_settings
from app.db.base import Base
from app.db import models  # noqa: F401
from app.db.session import engine
from app.security.csrf import CSRFMiddleware
from app.security.rate_limit import limiter
from sqlalchemy import inspect


settings = get_settings()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


def check_database_state() -> tuple[bool, str | None]:
    try:
        inspector = inspect(engine)
        model_tables = set(Base.metadata.tables)
        missing_tables = sorted(table_name for table_name in model_tables if not inspector.has_table(table_name))
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", exc)
        return False, "Database connection failed"

    if missing_tables:
        missing = ", ".join(missing_tables)
        return False, f"Database schema is not ready. Missing tables: {missing}"

    return True, None


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup complete")
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(status_code=429, content={"detail": "Too many requests"}),
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)
app.add_middleware(
    CSRFMiddleware,
    settings=settings,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age,
    session_cookie=settings.session_cookie_name,
    same_site=settings.session_same_site,
    https_only=settings.session_https_only or settings.app_env == "production",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(labs.router)
app.include_router(equipments.router)
app.include_router(reservations.router)
app.include_router(maintenance.router)
app.include_router(borrowings.router)
app.include_router(penalties.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(staff.router)
app.include_router(reports.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "client_ip": get_remote_address(request),
            "static_version": "20260419-reservation-autoapprove-1",
        },
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/healthz")
def health_check():
    return {"status": "ok", "app": settings.app_name}


@app.get("/readyz")
def readiness_check():
    database_ready, detail = check_database_state()
    if not database_ready:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "app": settings.app_name, "detail": detail},
        )
    return {"status": "ok", "app": settings.app_name}
