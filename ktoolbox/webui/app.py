from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, cast

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from ktoolbox import __version__
from ktoolbox.configuration import RuntimeContext
from ktoolbox.webui.auth import SESSION_COOKIE, AuthService, client_identifier
from ktoolbox.webui.database import WebUIDatabase, WebUISession
from ktoolbox.webui.models import (
    HealthResponse,
    LoginRequest,
    ProjectSummaryResponse,
    SessionResponse,
)


def auth_service(request: Request) -> AuthService:
    return cast(AuthService, request.app.state.auth)


async def require_session(request: Request) -> WebUISession:
    return await auth_service(request).session(request.cookies.get(SESSION_COOKIE))


async def require_csrf(
    request: Request,
    session: Annotated[WebUISession, Depends(require_session)],
) -> WebUISession:
    auth_service(request).verify_csrf(request, session)
    return session


def create_app(context: RuntimeContext) -> FastAPI:
    database = WebUIDatabase(context.project_root / ".ktoolbox" / "webui.sqlite3")
    auth = AuthService(context.configuration.webui, database)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        auth.validate_configuration()
        await database.initialize()
        yield

    app = FastAPI(
        title="KToolBox WebUI API",
        version=__version__.lstrip("v"),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.runtime_context = context
    app.state.database = database
    app.state.auth = auth

    @app.middleware("http")
    async def security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.post("/api/v1/session/login", response_model=SessionResponse)
    async def login(payload: LoginRequest, request: Request, response: Response) -> SessionResponse:
        result = await auth.login(payload.username, payload.password, client_identifier(request))
        response.set_cookie(
            SESSION_COOKIE,
            result.token,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="strict",
            max_age=context.configuration.webui.session_absolute_hours * 3600,
            path="/",
        )
        return SessionResponse(
            username=result.session.username,
            csrf_token=result.session.csrf_token,
            created_at=result.session.created_at,
        )

    @app.get("/api/v1/session", response_model=SessionResponse)
    async def current_session(
        session: Annotated[WebUISession, Depends(require_session)],
    ) -> SessionResponse:
        return SessionResponse(
            username=session.username,
            csrf_token=session.csrf_token,
            created_at=session.created_at,
        )

    @app.post("/api/v1/session/logout", status_code=status.HTTP_204_NO_CONTENT)
    async def logout(
        request: Request,
        _: Annotated[WebUISession, Depends(require_csrf)],
    ) -> Response:
        await auth.logout(request.cookies.get(SESSION_COOKIE))
        logout_response = Response(status_code=status.HTTP_204_NO_CONTENT)
        logout_response.delete_cookie(SESSION_COOKIE, path="/")
        return logout_response

    @app.get("/api/v1/project", response_model=ProjectSummaryResponse)
    async def project(
        _: Annotated[WebUISession, Depends(require_session)],
    ) -> ProjectSummaryResponse:
        root: Path = context.project_root
        return ProjectSummaryResponse(
            name=root.name,
            root=root,
            project_config=root / "ktoolbox.toml",
            dotenv_files=[root / ".env", root / "prod.env"],
            version=__version__,
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(error)})

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)

    return app
