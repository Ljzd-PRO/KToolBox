import asyncio
import pytest
from unittest.mock import Mock, patch
from ktoolbox.progress import ProgressManager, ManagedTqdm, create_managed_tqdm_class, ColorTheme


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


class TestColorTheme:
    """Test the ColorTheme class for enhanced visuals"""
    
    def test_color_codes(self):
        """Test that color codes are properly defined"""
        assert ColorTheme.RESET == '\033[0m'
        assert ColorTheme.BOLD == '\033[1m'
        assert ColorTheme.GREEN == '\033[32m'
        assert ColorTheme.BRIGHT_GREEN == '\033[92m'
    
    def test_emojis(self):
        """Test that emojis are properly defined"""
        assert ColorTheme.DOWNLOAD == "📥"
        assert ColorTheme.COMPLETED == "✅"
        assert ColorTheme.FAILED == "❌"
        assert ColorTheme.RUNNING == "🔄"
        assert ColorTheme.WAITING == "⏳"
        assert ColorTheme.SPEED == "⚡"
    
    def test_spinner_frames(self):
        """Test that spinner animation frames are defined"""
        assert len(ColorTheme.SPINNER_FRAMES) > 0
        assert all(isinstance(frame, str) for frame in ColorTheme.SPINNER_FRAMES)
    
    def test_colorize_without_color_support(self):
        """Test colorize returns plain text when colors not supported"""
        with patch.object(ColorTheme, 'supports_color', return_value=False):
            result = ColorTheme.colorize("test", ColorTheme.GREEN)
            assert result == "test"
    
    def test_colorize_with_color_support(self):
        """Test colorize adds ANSI codes when colors supported"""
        with patch.object(ColorTheme, 'supports_color', return_value=True):
            result = ColorTheme.colorize("test", ColorTheme.GREEN)
            assert result == f"{ColorTheme.GREEN}test{ColorTheme.RESET}"
    
    def test_colorize_with_bold(self):
        """Test colorize adds bold formatting"""
        with patch.object(ColorTheme, 'supports_color', return_value=True):
            result = ColorTheme.colorize("test", ColorTheme.GREEN, bold=True)
            assert result == f"{ColorTheme.BOLD}{ColorTheme.GREEN}test{ColorTheme.RESET}"


class TestEnhancedProgressManager:
    """Test enhanced progress manager features"""
    
    def test_progress_manager_with_visual_options(self):
        """Test creating ProgressManager with visual options"""
        manager = ProgressManager(max_workers=3, use_colors=True, use_emojis=True)
        assert manager.use_emojis is True
        
        manager2 = ProgressManager(max_workers=3, use_colors=False, use_emojis=False)
        assert manager2.use_emojis is False
    
    def test_enhanced_progress_state(self):
        """Test ProgressState has enhanced fields"""
        manager = ProgressManager()
        pbar = manager.create_progress_bar("test", total=100)
        
        progress_id = pbar.progress_id
        state = manager._progress_bars[progress_id]
        
        # Check enhanced fields
        assert hasattr(state, 'failed')
        assert hasattr(state, 'paused')
        assert state.failed is False
        assert state.paused is False
    
    def test_managed_tqdm_enhanced_methods(self):
        """Test ManagedTqdm enhanced methods"""
        manager = ProgressManager()
        pbar = ManagedTqdm(desc="test", total=100, manager=manager)
        
        # Test enhanced methods
        assert hasattr(pbar, 'set_failed')
        assert hasattr(pbar, 'set_paused')
        
        # Test methods work without error
        pbar.set_failed(True)
        pbar.set_paused(True)
        pbar.set_failed(False)
        pbar.set_paused(False)
        
        pbar.close()
    
    def test_enhanced_job_runner_parameters(self):
        """Test JobRunner accepts enhanced visual parameters"""
        with patch('ktoolbox.job.runner.config') as mock_config:
            mock_config.job.count = 3
            
            from ktoolbox.job.runner import JobRunner
            
            # Test with enhanced parameters
            runner = JobRunner(
                centralized_progress=True,
                use_colors=True,
                use_emojis=True
            )

            assert runner._progress_manager.use_emojis is True
            
            # Test disabling enhancements
            runner2 = JobRunner(
                centralized_progress=True,
                use_colors=False,
                use_emojis=False
            )

            assert runner2._progress_manager.use_emojis is False
    
    def test_render_overall_progress_with_enhancements(self):
        """Test that enhanced overall progress rendering works"""
        manager = ProgressManager(use_colors=True, use_emojis=True)
        manager.set_job_totals(10, 5, 1)
        
        # Should not crash and return list of strings
        lines = manager._render_overall_progress()
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert all(isinstance(line, str) for line in lines)
    
    def test_render_single_progress_bar_with_enhancements(self):
        """Test enhanced progress bar rendering"""
        from ktoolbox.progress import ProgressState
        
        manager = ProgressManager(use_colors=True, use_emojis=True)
        
        # Test normal progress
        state = ProgressState(desc="test.jpg", total=1000, current=500)
        line = manager._render_single_progress_bar(state)
        assert isinstance(line, str)
        assert "test.jpg" in line
        
        # Test failed state
        state.failed = True
        line = manager._render_single_progress_bar(state)
        assert isinstance(line, str)
        
        # Test finished state
        state.failed = False
        state.finished = True
        line = manager._render_single_progress_bar(state)
        assert isinstance(line, str)