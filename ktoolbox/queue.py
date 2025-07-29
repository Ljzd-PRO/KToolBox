"""Queue management for sync-creator operations"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from loguru import logger
from pydantic import BaseModel, Field, field_validator
from pathvalidate import sanitize_filename

from ktoolbox.model import BaseKToolBoxData
from ktoolbox.utils import parse_webpage_url

__all__ = ["QueueItem", "SyncCreatorQueue", "get_default_queue_path", "load_queue", "save_queue"]


class QueueItem(BaseModel):
    """
    A single item in the sync-creator queue
    
    :ivar url: The creator URL (if provided)
    :ivar service: The service name
    :ivar creator_id: The creator ID
    :ivar path: Download path for this creator
    :ivar added_at: When this item was added to the queue
    :ivar save_creator_indices: Whether to save creator indices
    :ivar mix_posts: Whether to mix posts from different posts at same path
    :ivar start_time: Start time filter for posts
    :ivar end_time: End time filter for posts
    :ivar offset: Result offset
    :ivar length: Number of posts to fetch
    """
    url: Optional[str] = None
    service: str
    creator_id: str
    path: Optional[Path] = None
    added_at: datetime = Field(default_factory=datetime.now)
    save_creator_indices: bool = False
    mix_posts: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    offset: int = 0
    length: Optional[int] = None
    
    @field_validator('path', mode='before')
    def validate_path(cls, v):
        if v is None:
            return None
        return Path(v) if not isinstance(v, Path) else v
    
    @classmethod
    def from_url(cls, url: str, path: Optional[Union[Path, str]] = None, **kwargs) -> "QueueItem":
        """Create a QueueItem from a creator URL"""
        service, creator_id, _ = parse_webpage_url(url)
        return cls(
            url=url,
            service=service,
            creator_id=creator_id,
            path=Path(path) if path else None,
            **kwargs
        )
    
    @classmethod
    def from_params(cls, service: str, creator_id: str, path: Optional[Union[Path, str]] = None, **kwargs) -> "QueueItem":
        """Create a QueueItem from service and creator_id"""
        return cls(
            service=service,
            creator_id=creator_id,
            path=Path(path) if path else None,
            **kwargs
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = self.model_dump()
        # Convert Path objects to strings
        if data.get('path'):
            data['path'] = str(data['path'])
        # Convert datetime to ISO string
        if data.get('added_at'):
            data['added_at'] = data['added_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "QueueItem":
        """Create from dictionary (JSON deserialization)"""
        # Parse datetime string
        if data.get('added_at') and isinstance(data['added_at'], str):
            data['added_at'] = datetime.fromisoformat(data['added_at'])
        # Parse Path string
        if data.get('path') and isinstance(data['path'], str):
            data['path'] = Path(data['path'])
        return cls(**data)


class SyncCreatorQueue(BaseKToolBoxData):
    """
    Sync creator queue data model
    
    For managing a queue of creators to sync.
    """
    items: List[QueueItem] = Field(default_factory=list)
    """Queue items"""
    
    def add_item(self, item: QueueItem) -> None:
        """Add an item to the queue"""
        self.items.append(item)
    
    def remove_item(self, index: int) -> Optional[QueueItem]:
        """Remove an item from the queue by index"""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def clear(self) -> None:
        """Clear all items from the queue"""
        self.items.clear()
    
    def is_empty(self) -> bool:
        """Check if the queue is empty"""
        return len(self.items) == 0
    
    def size(self) -> int:
        """Get the number of items in the queue"""
        return len(self.items)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "items": [item.to_dict() for item in self.items]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SyncCreatorQueue":
        """Create from dictionary (JSON deserialization)"""
        items = [QueueItem.from_dict(item_data) for item_data in data.get("items", [])]
        return cls(items=items)


def get_default_queue_path() -> Path:
    """Get the default path for the queue file"""
    ktoolbox_dir = Path.home() / ".ktoolbox"
    ktoolbox_dir.mkdir(exist_ok=True)
    return ktoolbox_dir / "sync_creator_queue.json"


def load_queue(queue_path: Optional[Path] = None) -> SyncCreatorQueue:
    """
    Load the sync creator queue from file
    
    :param queue_path: Path to the queue file, defaults to default location
    :return: The loaded queue or empty queue if file doesn't exist
    """
    if queue_path is None:
        queue_path = get_default_queue_path()
    
    if not queue_path.exists():
        logger.debug(f"Queue file not found at {queue_path}, returning empty queue")
        return SyncCreatorQueue()
    
    try:
        with open(queue_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        queue = SyncCreatorQueue.from_dict(data)
        logger.debug(f"Loaded queue with {queue.size()} items from {queue_path}")
        return queue
    except Exception as e:
        logger.error(f"Failed to load queue from {queue_path}: {e}")
        return SyncCreatorQueue()


def save_queue(queue: SyncCreatorQueue, queue_path: Optional[Path] = None) -> bool:
    """
    Save the sync creator queue to file
    
    :param queue: The queue to save
    :param queue_path: Path to save the queue file, defaults to default location
    :return: True if successful, False otherwise
    """
    if queue_path is None:
        queue_path = get_default_queue_path()
    
    try:
        # Ensure directory exists
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(queue_path, 'w', encoding='utf-8') as f:
            json.dump(queue.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved queue with {queue.size()} items to {queue_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save queue to {queue_path}: {e}")
        return False