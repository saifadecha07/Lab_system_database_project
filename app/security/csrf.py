from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import Settings
from app.security.session import get_csrf_token


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.header_name = settings.csrf_header_name
        self.header_lookup_name = self.header_name.lower()
        self.exempt_paths = set(settings.csrf_exempt_paths)

    async def dispatch(self, request: Request, call_next):
        if self._requires_csrf(request):
            session_token = get_csrf_token(request)
            header_token = request.headers.get(self.header_lookup_name)
            if not session_token or session_token != header_token:
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        response = await call_next(request)
        csrf_token = get_csrf_token(request)
        if csrf_token:
            response.headers[self.header_name] = csrf_token
        return response

    def _requires_csrf(self, request: Request) -> bool:
        if request.method in SAFE_METHODS:
            return False
        if request.url.path in self.exempt_paths:
            return False
        return "user_id" in request.session
