"""FastAPI application factory"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from ..configuration import config
from .routers import auth, api, websocket

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="KToolBox Web UI",
        description="Web interface for KToolBox - Kemono content downloader",
        version="1.0.0",
        docs_url="/docs" if config.webui.debug else None,
        redoc_url="/redoc" if config.webui.debug else None,
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    app.include_router(api.router, prefix="/api", tags=["api"])
    app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
    
    # Serve static files (built frontend)
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Serve React app
        @app.get("/{path:path}")
        async def serve_frontend(path: str = ""):
            """Serve the React frontend for all non-API routes"""
            index_file = static_path / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            raise HTTPException(status_code=404, detail="Frontend not built")
    else:
        @app.get("/")
        async def root():
            return {"message": "KToolBox Web UI - Frontend not built. Please build the frontend first."}
    
    return app