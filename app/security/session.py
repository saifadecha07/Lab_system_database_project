import secrets

from fastapi import Request, Response


def start_user_session(request: Request, user_id: int) -> None:
    request.session.clear()
    request.session["user_id"] = user_id
    request.session["csrf_token"] = secrets.token_urlsafe(32)


def clear_user_session(request: Request, response: Response, cookie_name: str) -> None:
    request.session.clear()
    response.delete_cookie(cookie_name)


def get_csrf_token(request: Request) -> str | None:
    return request.session.get("csrf_token")
