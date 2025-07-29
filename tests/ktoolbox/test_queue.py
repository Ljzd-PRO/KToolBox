import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ktoolbox.queue import QueueItem, SyncCreatorQueue, load_queue, save_queue
from ktoolbox.cli import KToolBoxCli


class TestQueueItem:
    def test_from_url(self):
        """Test creating QueueItem from URL"""
        url = "https://kemono.cr/fanbox/user/9016"
        item = QueueItem.from_url(url, path="/test/path")
        
        assert item.url == url
        assert item.service == "fanbox"
        assert item.creator_id == "9016"
        assert item.path == Path("/test/path")
        
    def test_from_params(self):
        """Test creating QueueItem from service and creator_id"""
        item = QueueItem.from_params("patreon", "12345", path="/test/path")
        
        assert item.url is None
        assert item.service == "patreon"
        assert item.creator_id == "12345"
        assert item.path == Path("/test/path")
        
    def test_to_dict_from_dict(self):
        """Test serialization and deserialization"""
        original = QueueItem.from_url(
            "https://kemono.cr/fanbox/user/9016",
            path="/test/path",
            save_creator_indices=True,
            length=10
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = QueueItem.from_dict(data)
        
        assert restored.url == original.url
        assert restored.service == original.service
        assert restored.creator_id == original.creator_id
        assert restored.path == original.path
        assert restored.save_creator_indices == original.save_creator_indices
        assert restored.length == original.length
        assert abs((restored.added_at - original.added_at).total_seconds()) < 1  # Close enough


class TestSyncCreatorQueue:
    def test_empty_queue(self):
        """Test empty queue operations"""
        queue = SyncCreatorQueue()
        
        assert queue.is_empty()
        assert queue.size() == 0
        
    def test_add_remove_items(self):
        """Test adding and removing items"""
        queue = SyncCreatorQueue()
        item1 = QueueItem.from_url("https://kemono.cr/fanbox/user/9016")
        item2 = QueueItem.from_params("patreon", "12345")
        
        # Add items
        queue.add_item(item1)
        queue.add_item(item2)
        
        assert queue.size() == 2
        assert not queue.is_empty()
        
        # Remove item
        removed = queue.remove_item(0)
        assert removed == item1
        assert queue.size() == 1
        
        # Invalid remove
        invalid_remove = queue.remove_item(10)
        assert invalid_remove is None
        assert queue.size() == 1
        
        # Clear queue
        queue.clear()
        assert queue.is_empty()
        assert queue.size() == 0
        
    def test_serialization(self):
        """Test queue serialization"""
        queue = SyncCreatorQueue()
        queue.add_item(QueueItem.from_url("https://kemono.cr/fanbox/user/9016"))
        queue.add_item(QueueItem.from_params("patreon", "12345"))
        
        # Convert to dict and back
        data = queue.to_dict()
        restored = SyncCreatorQueue.from_dict(data)
        
        assert restored.size() == queue.size()
        assert restored.items[0].service == queue.items[0].service
        assert restored.items[0].creator_id == queue.items[0].creator_id


class TestQueueFileOperations:
    def test_save_load_queue(self):
        """Test saving and loading queue from file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            queue_path = Path(tmp_dir) / "test_queue.json"
            
            # Create and save queue
            original_queue = SyncCreatorQueue()
            original_queue.add_item(QueueItem.from_url("https://kemono.cr/fanbox/user/9016"))
            original_queue.add_item(QueueItem.from_params("patreon", "12345"))
            
            assert save_queue(original_queue, queue_path)
            assert queue_path.exists()
            
            # Load queue
            loaded_queue = load_queue(queue_path)
            
            assert loaded_queue.size() == original_queue.size()
            assert loaded_queue.items[0].service == original_queue.items[0].service
            assert loaded_queue.items[0].creator_id == original_queue.items[0].creator_id
            
    def test_load_nonexistent_queue(self):
        """Test loading a queue that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            queue_path = Path(tmp_dir) / "nonexistent_queue.json"
            
            loaded_queue = load_queue(queue_path)
            
            assert loaded_queue.is_empty()


@pytest.mark.asyncio
class TestQueueCLI:
    async def test_queue_operations(self):
        """Test basic queue CLI operations"""
        # Start with clear queue
        await KToolBoxCli.queue_clear()
        
        # Test empty queue list
        result = await KToolBoxCli.queue_list()
        assert "Queue is empty" in result
        
        # Add item to queue
        result = await KToolBoxCli.queue_add(
            url="https://kemono.cr/fanbox/user/9016",
            path="./test_downloads"
        )
        assert "Added creator" in result and "fanbox/9016" in result
        
        # List queue with item
        result = await KToolBoxCli.queue_list()
        assert "fanbox/9016" in result
        assert "1 items" in result
        
        # Add another item using service/creator_id
        result = await KToolBoxCli.queue_add(
            service="patreon",
            creator_id="12345",
            length=5
        )
        assert "Added creator" in result and "patreon/12345" in result
        
        # List updated queue
        result = await KToolBoxCli.queue_list()
        assert "2 items" in result
        assert "fanbox/9016" in result
        assert "patreon/12345" in result
        assert "length=5" in result
        
        # Remove item by index
        result = await KToolBoxCli.queue_remove(0)
        assert "Removed creator" in result and "fanbox/9016" in result
        
        # List after removal
        result = await KToolBoxCli.queue_list()
        assert "1 items" in result
        assert "patreon/12345" in result
        assert "fanbox/9016" not in result
        
        # Test invalid remove
        result = await KToolBoxCli.queue_remove(10)
        assert "Invalid index" in result
        
        # Clear queue
        result = await KToolBoxCli.queue_clear()
        assert "Cleared 1 items" in result
        
        # Verify empty
        result = await KToolBoxCli.queue_list()
        assert "Queue is empty" in result
        
    async def test_invalid_queue_add(self):
        """Test adding invalid items to queue"""
        # Missing required parameters
        result = await KToolBoxCli.queue_add()
        assert "MissingParams" in result or "use_at_lease_one" in result
        
        # Invalid URL
        result = await KToolBoxCli.queue_add(url="")
        assert "MissingParams" in result or "use_at_lease_one" in result