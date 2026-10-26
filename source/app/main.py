import logging
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo.errors import PyMongoError
from app.core.config import Settings
from app.core.errors import DomainError
from app.db.mongo import client_for, initialize
from app.api.routes import router
from app.api.question_routes import router as question_router
from app.core.body_limit import BodyLimitMiddleware

ROOT = Path(__file__).parent


def create_app(settings=None, database=None):
    cfg = settings or Settings()
    if len(cfg.session_secret) < 32 or cfg.session_secret.startswith("replace-"):
        raise RuntimeError("Set SESSION_SECRET to a random value of at least 32 characters. See .env.example.")
    if cfg.environment == "production" and (not cfg.cookie_secure or not cfg.base_url.startswith("https://")):
        raise RuntimeError("Production requires HTTPS and COOKIE_SECURE=true")

    @asynccontextmanager
    async def lifespan(app):
        client = None
        if database is None:
            client = client_for(cfg.mongo_uri)
            if not client.admin.command("hello").get("setName"):
                client.close()
                raise RuntimeError("MongoDB replica set required for safe multi-document transactions")
            app.state.db = client[cfg.mongo_db]
        else: app.state.db = database
        initialize(app.state.db)
        yield
        if client is not None: client.close()

    application = FastAPI(title="问卷工坊 · MongoDB Survey", version="2.0.0", lifespan=lifespan)
    application.state.settings = cfg
    application.add_middleware(BodyLimitMiddleware)

    @application.middleware("http")
    async def guard(request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Prevent login/register CSRF too: reject an explicit foreign browser Origin.
            origin = request.headers.get("origin")
            allowed = urlparse(cfg.base_url)
            if origin and origin != f"{allowed.scheme}://{allowed.netloc}":
                return JSONResponse({"error": {"code": "CSRF_FAILED", "message": "请求来源不受信任", "details": {}}}, 403)
            try: length = int(request.headers.get("content-length", "0"))
            except ValueError: length = 2_097_153
            if length > 2_097_152:
                return JSONResponse({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "请求超出 2MiB", "details": {}}}, 413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if not request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(DomainError)
    async def domain_handler(request, exc):
        return JSONResponse({"error": {"code": exc.code, "message": exc.message, "details": exc.details}}, exc.status)

    @application.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        # Never echo the invalid request body (passwords/anonymous answer data).
        fields = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "VALIDATION_ERROR", "message": "请求参数有误", "details": {"fields": fields}}}, 422)

    @application.exception_handler(PyMongoError)
    async def mongo_handler(request, exc):
        logging.getLogger(__name__).error("Mongo operation failed: %s", type(exc).__name__)
        return JSONResponse({"error": {"code": "DATABASE_UNAVAILABLE", "message": "数据库暂不可用，请稍后重试", "details": {}}}, 503)

    application.include_router(router)
    application.include_router(question_router)
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @application.get("/health")
    def health():
        application.state.db.command("ping")
        return {"status": "ok"}

    for path in ("/", "/login", "/register", "/dashboard", "/questions", "/questions/{question_id}", "/question-banks", "/question-banks/{bank_id}", "/surveys/new", "/surveys/{survey_id}/edit", "/surveys/{survey_id}/preview", "/surveys/{survey_id}/statistics", "/survey/{public_id}"):
        application.add_api_route(path, lambda: FileResponse(ROOT / "templates" / "index.html"), methods=["GET"], include_in_schema=False)
    return application


app = create_app()
