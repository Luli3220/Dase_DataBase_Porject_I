import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request
from app.core.errors import require, DomainError
from app.db.mongo import oid

COOKIE = "survey_session"


def codec(request):
    return URLSafeTimedSerializer(request.app.state.settings.session_secret, salt="survey-session-v1")


def session_data(request):
    token = request.cookies.get(COOKIE)
    require(token is not None, "请先登录", "UNAUTHENTICATED", 401)
    try:
        data = codec(request).loads(token, max_age=request.app.state.settings.session_max_age)
        require(isinstance(data, dict) and isinstance(data.get("uid"), str) and isinstance(data.get("csrf"), str), "会话无效", "UNAUTHENTICATED", 401)
        return data
    except (BadSignature, SignatureExpired):
        raise DomainError("SESSION_EXPIRED", "登录已过期，请重新登录", 401)


def current_user(request: Request):
    data = session_data(request)
    user = request.app.state.db.users.find_one({"_id": oid(data["uid"])})
    require(user is not None, "会话无效", "UNAUTHENTICATED", 401)
    require(data.get("sessionVersion") == user.get("sessionVersion", 1), "会话已退出，请重新登录", "SESSION_EXPIRED", 401)
    return user


def csrf_user(request: Request):
    user = current_user(request)
    expected, supplied = session_data(request)["csrf"], request.headers.get("X-CSRF-Token", "")
    require(secrets.compare_digest(expected, supplied), "CSRF 校验失败，请刷新", "CSRF_FAILED", 403)
    return user


def set_session(request, response, user):
    csrf = secrets.token_urlsafe(24)
    token = codec(request).dumps({"uid": str(user["_id"]), "csrf": csrf, "sessionVersion": user.get("sessionVersion", 1)})
    cfg = request.app.state.settings
    response.set_cookie(COOKIE, token, httponly=True, secure=cfg.cookie_secure, samesite="lax", max_age=cfg.session_max_age, path="/")
    return csrf
