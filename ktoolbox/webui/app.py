from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import RequestResponseEndpoint

from ktoolbox import __version__
from ktoolbox.configuration import RuntimeContext
from ktoolbox.project_config import ProjectConfigStore
from ktoolbox.webui.auth import (
    SESSION_COOKIE,
    AuthService,
    client_identifier,
    require_csrf,
    require_session,
)
from ktoolbox.webui.creator_profiles import CreatorClientFactory, CreatorProfileCache, CreatorRosterService
from ktoolbox.webui.database import WebUIDatabase, WebUISession
from ktoolbox.webui.error_responses import error_payload, validation_error_payload
from ktoolbox.webui.filesystem import FilesystemBrowser
from ktoolbox.webui.filesystem_routes import create_filesystem_router
from ktoolbox.webui.models import (
    HealthResponse,
    LoginRequest,
    ProjectSummaryResponse,
    SessionResponse,
)
from ktoolbox.webui.openapi_contract import build_openapi_schema, stable_operation_id
from ktoolbox.webui.pawchive_routes import create_pawchive_router
from ktoolbox.webui.project_lock import ProjectProcessLock
from ktoolbox.webui.project_routes import create_project_router
from ktoolbox.webui.task_executor import TaskExecutor
from ktoolbox.webui.task_routes import create_task_router
from ktoolbox.webui.task_scheduler import TaskScheduler
from ktoolbox.webui.task_store import TaskStore


def create_app(
    context: RuntimeContext,
    *,
    task_executor: TaskExecutor | None = None,
    creator_client_factory: CreatorClientFactory | None = None,
    filesystem_browser: FilesystemBrowser | None = None,
) -> FastAPI:
    database = WebUIDatabase(context.project_root / ".ktoolbox" / "webui.sqlite3")
    auth = AuthService(context.configuration.webui, database)
    task_store = TaskStore(database)
    task_scheduler = TaskScheduler(
        context,
        task_store,
        max_concurrency=context.configuration.webui.max_active_tasks,
        executor=task_executor,
    )
    creator_roster = CreatorRosterService(
        ProjectConfigStore(context.project_root / "ktoolbox.toml"),
        CreatorProfileCache(database),
        client_factory=creator_client_factory,
    )
    project_lock = ProjectProcessLock(context.project_root / ".ktoolbox" / "webui.lock")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        auth.validate_configuration()
        await project_lock.acquire()
        try:
            await database.initialize()
            await task_scheduler.start()
            yield
        finally:
            await task_scheduler.stop()
            await project_lock.release()

    app = FastAPI(
        title="KToolBox WebUI API",
        version=__version__.lstrip("v"),
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
        generate_unique_id_function=stable_operation_id,
    )
    app.openapi = lambda: build_openapi_schema(app)  # type: ignore[method-assign]
    app.state.runtime_context = context
    app.state.database = database
    app.state.auth = auth
    app.state.task_store = task_store
    app.state.task_scheduler = task_scheduler
    browser = filesystem_browser or FilesystemBrowser(context.project_root)
    app.state.filesystem_browser = browser
    app.include_router(create_project_router(context.project_root, creator_roster))
    app.include_router(create_filesystem_router(browser))
    app.include_router(create_pawchive_router())
    app.include_router(create_task_router(context.project_root))

    static_root = Path(__file__).parent / "static"
    assets_root = static_root / "assets"
    if assets_root.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_root), name="webui-assets")

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
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
        return JSONResponse(status_code=code, content=error_payload(str(error), code))

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
        return JSONResponse(status_code=code, content=validation_error_payload(error.errors(), code))

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=error_payload(error.detail, error.status_code),
            headers=error.headers,
        )

    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str) -> FileResponse:
        index = static_root / "index.html"
        if path.startswith("api/") or not index.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return app
