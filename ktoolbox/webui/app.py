"""FastAPI web application for KToolBox"""
import asyncio
import os
import signal
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from loguru import logger

from ktoolbox.cli import KToolBoxCli


# Task tracking
tasks: Dict[str, Dict[str, Any]] = {}


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class SearchCreatorRequest(BaseModel):
    name: Optional[str] = None
    id: Optional[str] = None
    service: Optional[str] = None


class SearchCreatorPostRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    service: Optional[str] = None
    q: Optional[str] = None
    o: Optional[int] = None


class GetPostRequest(BaseModel):
    service: str
    creator_id: str
    post_id: str
    revision_id: Optional[str] = None


class DownloadPostRequest(BaseModel):
    url: Optional[str] = None
    service: Optional[str] = None
    creator_id: Optional[str] = None
    post_id: Optional[str] = None
    revision_id: Optional[str] = None
    path: str = "."
    dump_post_data: bool = True


class SyncCreatorRequest(BaseModel):
    url: Optional[str] = None
    service: Optional[str] = None
    creator_id: Optional[str] = None
    path: str = "."
    save_creator_indices: bool = False
    mix_posts: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    offset: int = 0
    length: Optional[int] = None
    keywords: Optional[str] = None
    keywords_exclude: Optional[str] = None


def update_task_status(task_id: str, status: str, result: Any = None, error: str = None, progress: Dict[str, Any] = None):
    """Update task status in the global tasks dictionary"""
    if task_id in tasks:
        tasks[task_id]["status"] = status
        if result is not None:
            tasks[task_id]["result"] = result
        if error is not None:
            tasks[task_id]["error"] = error
        if progress is not None:
            tasks[task_id]["progress"] = progress


async def run_task(task_id: str, coro):
    """Run an async task and update its status"""
    try:
        update_task_status(task_id, "running")
        result = await coro
        update_task_status(task_id, "completed", result=result)
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        update_task_status(task_id, "failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting KToolBox WebUI...")
    yield
    # Shutdown
    logger.info("Shutting down KToolBox WebUI...")


# Create FastAPI app
app = FastAPI(
    title="KToolBox WebUI",
    description="Web interface for KToolBox - A useful tool for downloading posts in Kemono.cr / .su / .party",
    version="0.20.0",
    lifespan=lifespan
)

# Get the directory where this file is located
webui_dir = Path(__file__).parent
static_dir = webui_dir / "static"

# Mount static files if they exist
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML page"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file))
    else:
        # Return a simple placeholder if frontend is not built yet
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>KToolBox WebUI</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .placeholder { text-align: center; margin-top: 100px; }
                .placeholder h1 { color: #333; }
                .placeholder p { color: #666; margin: 20px 0; }
                .api-link { color: #007bff; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="placeholder">
                <h1>KToolBox WebUI</h1>
                <p>Frontend is not built yet. Please run the frontend build process.</p>
                <p>You can access the API documentation at <a href="/docs" class="api-link">/docs</a></p>
            </div>
        </body>
        </html>
        """


# API Routes
@app.get("/api/version")
async def get_version():
    """Get KToolBox version"""
    return {"version": await KToolBoxCli.version()}


@app.get("/api/site-version")
async def get_site_version():
    """Get current Kemono site app commit hash"""
    return {"site_version": await KToolBoxCli.site_version()}


@app.get("/api/example-env")
async def get_example_env():
    """Get example configuration env content"""
    # Capture the output that would normally be printed
    import io
    import sys
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        await KToolBoxCli.example_env()
    return {"env_content": f.getvalue()}


@app.post("/api/search-creator")
async def search_creator(request: SearchCreatorRequest, background_tasks: BackgroundTasks):
    """Search creator, you can use multiple parameters as keywords"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "type": "search_creator"
    }
    
    # Run the task in background
    background_tasks.add_task(
        run_task,
        task_id,
        KToolBoxCli.search_creator(
            name=request.name,
            id=request.id,
            service=request.service
        )
    )
    
    return TaskResponse(task_id=task_id, status="pending")


@app.post("/api/search-creator-post")
async def search_creator_post(request: SearchCreatorPostRequest, background_tasks: BackgroundTasks):
    """Search posts from creator"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "type": "search_creator_post"
    }
    
    # Run the task in background
    background_tasks.add_task(
        run_task,
        task_id,
        KToolBoxCli.search_creator_post(
            id=request.id,
            name=request.name,
            service=request.service,
            q=request.q,
            o=request.o
        )
    )
    
    return TaskResponse(task_id=task_id, status="pending")


@app.post("/api/get-post")
async def get_post(request: GetPostRequest, background_tasks: BackgroundTasks):
    """Get a specific post or revision"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "type": "get_post"
    }
    
    # Run the task in background
    background_tasks.add_task(
        run_task,
        task_id,
        KToolBoxCli.get_post(
            service=request.service,
            creator_id=request.creator_id,
            post_id=request.post_id,
            revision_id=request.revision_id
        )
    )
    
    return TaskResponse(task_id=task_id, status="pending")


@app.post("/api/download-post")
async def download_post(request: DownloadPostRequest, background_tasks: BackgroundTasks):
    """Download a specific post or revision"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "type": "download_post"
    }
    
    # Run the task in background
    background_tasks.add_task(
        run_task,
        task_id,
        KToolBoxCli.download_post(
            url=request.url,
            service=request.service,
            creator_id=request.creator_id,
            post_id=request.post_id,
            revision_id=request.revision_id,
            path=Path(request.path),
            dump_post_data=request.dump_post_data
        )
    )
    
    return TaskResponse(task_id=task_id, status="pending")


@app.post("/api/sync-creator")
async def sync_creator(request: SyncCreatorRequest, background_tasks: BackgroundTasks):
    """Sync posts from a creator"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "type": "sync_creator"
    }
    
    # Parse keywords if provided
    keywords = tuple(request.keywords.split(',')) if request.keywords else None
    keywords_exclude = tuple(request.keywords_exclude.split(',')) if request.keywords_exclude else None
    
    # Run the task in background
    background_tasks.add_task(
        run_task,
        task_id,
        KToolBoxCli.sync_creator(
            url=request.url,
            service=request.service,
            creator_id=request.creator_id,
            path=Path(request.path),
            save_creator_indices=request.save_creator_indices,
            mix_posts=request.mix_posts,
            start_time=request.start_time,
            end_time=request.end_time,
            offset=request.offset,
            length=request.length,
            keywords=keywords,
            keywords_exclude=keywords_exclude
        )
    )
    
    return TaskResponse(task_id=task_id, status="pending")


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        progress=task.get("progress")
    )


@app.get("/api/tasks")
async def get_all_tasks():
    """Get all tasks"""
    return {"tasks": list(tasks.values())}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks[task_id]
    return {"message": "Task deleted successfully"}


def start_webui(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    """Start the WebUI server"""
    
    def run_server():
        """Run the uvicorn server in a separate thread"""
        uvicorn.run(app, host=host, port=port, log_level="info")
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    if open_browser:
        # Give the server a moment to start up
        import time
        time.sleep(1.5)
        url = f"http://{host}:{port}"
        logger.info(f"Opening browser to {url}")
        webbrowser.open(url)
    
    try:
        # Keep the main thread alive
        logger.info(f"KToolBox WebUI is running on http://{host}:{port}")
        logger.info("Press Ctrl+C to stop the server")
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down WebUI...")
        os._exit(0)