"""Main API endpoints for CLI functionality"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
import asyncio
import uuid
from datetime import datetime

from ...cli import KToolBoxCli
from ...configuration import config
from ..auth import verify_credentials

router = APIRouter()

# Task management
active_tasks: Dict[str, asyncio.Task] = {}
task_results: Dict[str, Dict[str, Any]] = {}

class TaskResponse(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    message: str = ""

class ConfigResponse(BaseModel):
    """Configuration response model"""
    api: dict
    downloader: dict
    job: dict
    logger: dict
    webui: dict
    ssl_verify: bool
    json_dump_indent: int
    use_uvloop: bool

# Configuration endpoints
@router.get("/config", response_model=ConfigResponse)
async def get_config(username: str = Depends(verify_credentials)):
    """Get current configuration"""
    return ConfigResponse(
        api=config.api.model_dump(),
        downloader=config.downloader.model_dump(),
        job=config.job.model_dump(),
        logger=config.logger.model_dump(),
        webui=config.webui.model_dump(),
        ssl_verify=config.ssl_verify,
        json_dump_indent=config.json_dump_indent,
        use_uvloop=config.use_uvloop
    )

# Version endpoints
@router.get("/version")
async def get_version(username: str = Depends(verify_credentials)):
    """Get KToolBox version"""
    return {"version": await KToolBoxCli.version()}

@router.get("/site-version")
async def get_site_version(username: str = Depends(verify_credentials)):
    """Get Kemono site version"""
    result = await KToolBoxCli.site_version()
    return {"site_version": result}

# Search endpoints
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

@router.post("/search/creator")
async def search_creator(
    request: SearchCreatorRequest,
    username: str = Depends(verify_credentials)
):
    """Search for creators"""
    result = await KToolBoxCli.search_creator(
        name=request.name,
        id=request.id,
        service=request.service
    )
    return {"results": result}

@router.post("/search/creator-posts")
async def search_creator_posts(
    request: SearchCreatorPostRequest,
    username: str = Depends(verify_credentials)
):
    """Search posts from creator"""
    result = await KToolBoxCli.search_creator_post(
        id=request.id,
        name=request.name,
        service=request.service,
        q=request.q,
        o=request.o
    )
    return {"results": result}

# Post operations
class GetPostRequest(BaseModel):
    service: str
    creator_id: str
    post_id: str
    revision_id: Optional[str] = None

@router.post("/post/get")
async def get_post(
    request: GetPostRequest,
    username: str = Depends(verify_credentials)
):
    """Get a specific post"""
    result = await KToolBoxCli.get_post(
        service=request.service,
        creator_id=request.creator_id,
        post_id=request.post_id,
        revision_id=request.revision_id
    )
    return {"post": result}

# Download operations  
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

async def run_download_post_task(task_id: str, request: DownloadPostRequest):
    """Background task for downloading post"""
    try:
        task_results[task_id] = {"status": "running", "progress": 0}
        
        # Convert keywords to tuple if provided
        result = await KToolBoxCli.download_post(
            url=request.url,
            service=request.service,
            creator_id=request.creator_id,
            post_id=request.post_id,
            revision_id=request.revision_id,
            path=Path(request.path),
            dump_post_data=request.dump_post_data
        )
        
        task_results[task_id] = {
            "status": "completed",
            "result": result,
            "progress": 100
        }
    except Exception as e:
        task_results[task_id] = {
            "status": "failed",
            "error": str(e),
            "progress": 0
        }
    finally:
        if task_id in active_tasks:
            del active_tasks[task_id]

async def run_sync_creator_task(task_id: str, request: SyncCreatorRequest):
    """Background task for syncing creator"""
    try:
        task_results[task_id] = {"status": "running", "progress": 0}
        
        # Convert keywords to tuple if provided
        keywords_tuple = tuple(request.keywords.split(",")) if request.keywords else None
        keywords_exclude_tuple = tuple(request.keywords_exclude.split(",")) if request.keywords_exclude else None
        
        result = await KToolBoxCli.sync_creator(
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
            keywords=keywords_tuple,
            keywords_exclude=keywords_exclude_tuple
        )
        
        task_results[task_id] = {
            "status": "completed",
            "result": result,
            "progress": 100
        }
    except Exception as e:
        task_results[task_id] = {
            "status": "failed", 
            "error": str(e),
            "progress": 0
        }
    finally:
        if task_id in active_tasks:
            del active_tasks[task_id]

@router.post("/download/post", response_model=TaskResponse)
async def download_post(
    request: DownloadPostRequest,
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_credentials)
):
    """Download a specific post (async)"""
    task_id = str(uuid.uuid4())
    
    # Start background task
    task = asyncio.create_task(run_download_post_task(task_id, request))
    active_tasks[task_id] = task
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Download task started"
    )

@router.post("/sync/creator", response_model=TaskResponse)
async def sync_creator(
    request: SyncCreatorRequest,
    background_tasks: BackgroundTasks,
    username: str = Depends(verify_credentials)
):
    """Sync creator posts (async)"""
    task_id = str(uuid.uuid4())
    
    # Start background task
    task = asyncio.create_task(run_sync_creator_task(task_id, request))
    active_tasks[task_id] = task
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Sync task started"
    )

# Task management endpoints
@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    username: str = Depends(verify_credentials)
):
    """Get task status and result"""
    if task_id in task_results:
        return task_results[task_id]
    elif task_id in active_tasks:
        return {"status": "running", "progress": 0}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@router.get("/tasks")
async def list_tasks(username: str = Depends(verify_credentials)):
    """List all tasks"""
    tasks = {}
    
    # Add completed/failed tasks
    for task_id, result in task_results.items():
        tasks[task_id] = result
    
    # Add running tasks
    for task_id in active_tasks.keys():
        if task_id not in tasks:
            tasks[task_id] = {"status": "running", "progress": 0}
    
    return {"tasks": tasks}

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    username: str = Depends(verify_credentials)
):
    """Cancel a running task"""
    if task_id in active_tasks:
        active_tasks[task_id].cancel()
        del active_tasks[task_id]
        if task_id in task_results:
            task_results[task_id]["status"] = "cancelled"
        return {"message": "Task cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Task not found or not running")