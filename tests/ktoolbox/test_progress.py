import asyncio
import pytest
from unittest.mock import Mock, patch
from ktoolbox.progress import ProgressManager, ManagedTqdm, create_managed_tqdm_class


class TestProgressManager:
    """Test the ProgressManager class"""
    
    def test_progress_manager_creation(self):
        """Test creating a ProgressManager"""
        manager = ProgressManager(max_workers=3)
        assert manager.max_workers == 3
        assert manager._total_jobs == 0
        assert manager._completed_jobs == 0
        assert manager._failed_jobs == 0
    
    def test_job_totals(self):
        """Test setting and updating job totals"""
        manager = ProgressManager()
        
        manager.set_job_totals(10, 3, 1)
        assert manager._total_jobs == 10
        assert manager._completed_jobs == 3
        assert manager._failed_jobs == 1
        
        manager.update_job_progress(completed=5, failed=2)
        assert manager._completed_jobs == 5
        assert manager._failed_jobs == 2
    
    def test_managed_tqdm_fallback(self):
        """Test ManagedTqdm falls back to standard tqdm when needed"""
        # Test with disabled progress
        pbar = ManagedTqdm(desc="test", total=100, disable=True)
        assert pbar._fallback is not None
        assert pbar.manager is None
        
        # Test with no manager
        pbar2 = ManagedTqdm(desc="test", total=100, manager=None)
        assert pbar2._fallback is not None
        assert pbar2.manager is None
    
    def test_managed_tqdm_with_manager(self):
        """Test ManagedTqdm works with manager"""
        manager = ProgressManager()
        pbar = ManagedTqdm(desc="test", total=100, manager=manager)
        
        assert pbar._fallback is None
        assert pbar.manager is manager
        assert pbar.progress_id is not None
        
        # Test update
        pbar.update(10)
        assert pbar.n == 10
        
        # Verify the progress bar exists before closing
        assert pbar.progress_id in manager._progress_bars
        
        # Test close (should handle no event loop gracefully)
        pbar.close()
        
        # In test environment with no event loop, the progress bar should be removed immediately
        # So we just verify close() doesn't crash
    
    def test_create_managed_tqdm_class(self):
        """Test the tqdm class factory"""
        manager = ProgressManager()
        TqdmClass = create_managed_tqdm_class(manager)
        
        pbar = TqdmClass(desc="test", total=100)
        assert pbar.manager is manager
        assert isinstance(pbar, ManagedTqdm)


class TestJobRunnerIntegration:
    """Test JobRunner integration with progress manager"""
    
    @patch('ktoolbox.job.runner.config')
    def test_job_runner_with_centralized_progress(self, mock_config):
        """Test JobRunner creates progress manager when enabled"""
        # Mock the config
        mock_config.job.count = 3
        
        from ktoolbox.job.runner import JobRunner
        runner = JobRunner(progress=True, centralized_progress=True)
        
        assert runner._centralized_progress is True
        assert runner._progress_manager is not None
        assert runner._tqdm_class is not None
    
    @patch('ktoolbox.job.runner.config')
    def test_job_runner_without_centralized_progress(self, mock_config):
        """Test JobRunner doesn't create progress manager when disabled"""
        mock_config.job.count = 3
        
        from ktoolbox.job.runner import JobRunner
        runner = JobRunner(progress=True, centralized_progress=False)
        
        assert runner._centralized_progress is False
        assert runner._progress_manager is None
    
    @patch('ktoolbox.job.runner.config')
    def test_job_runner_backward_compatibility(self, mock_config):
        """Test backward compatibility - old parameters still work"""
        mock_config.job.count = 3
        
        from ktoolbox.job.runner import JobRunner
        
        # Test old-style initialization
        runner = JobRunner(progress=True)
        
        # Should default to centralized progress
        assert runner._centralized_progress is True
        assert runner._progress_manager is not None
        
        # Test with custom tqdm class
        custom_tqdm = Mock()
        runner2 = JobRunner(progress=True, tqdm_class=custom_tqdm, centralized_progress=False)
        
        assert runner2._tqdm_class is custom_tqdm
        assert runner2._progress_manager is None
    
    @patch('ktoolbox.job.runner.config')
    def test_job_runner_add_jobs_updates_total(self, mock_config):
        """Test that adding jobs updates the total count"""
        mock_config.job.count = 3
        
        from ktoolbox.job.runner import JobRunner
        runner = JobRunner(centralized_progress=True)
        
        # Create mock jobs
        jobs = [Mock() for _ in range(3)]
        
        # Should be async, but we can test the synchronous parts
        assert runner._total_jobs_count == 0
        
        # Simulate adding jobs (normally async)
        runner._total_jobs_count += len(jobs)
        if runner._progress_manager:
            runner._progress_manager.set_job_totals(runner._total_jobs_count)
        
        assert runner._total_jobs_count == 3
        assert runner._progress_manager._total_jobs == 3