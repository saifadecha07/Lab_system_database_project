from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


settings = get_settings()


def build_engine(database_url: str):
    url = make_url(database_url)
    engine_kwargs = {"pool_pre_ping": True}

    if url.get_backend_name() == "sqlite":
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if url.database in {None, "", ":memory:"}:
            engine_kwargs["poolclass"] = StaticPool
    else:
        engine_kwargs["pool_recycle"] = 1800
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10

    return create_engine(database_url, **engine_kwargs)


engine = build_engine(settings.database_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
