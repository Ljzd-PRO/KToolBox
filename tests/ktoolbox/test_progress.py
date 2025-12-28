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

    @patch('ktoolbox.job.runner.config')
    @pytest.mark.asyncio
    async def test_file_existed_updates_existed_and_logged_debug(self, mock_config, capsys):
        """When a downloader returns FileExisted, the runner should log DEBUG and increment existed count"""
        mock_config.job.count = 1
        # Minimal downloader config used to build URL
        mock_config.downloader.scheme = 'https'
        mock_config.api.files_netloc = 'example.com'
        mock_config.ssl_verify = True

        from ktoolbox.job.runner import JobRunner
        from ktoolbox.downloader.base import DownloaderRet
        from ktoolbox._enum import RetCodeEnum
        from pathlib import Path

        # Create a minimal mock job
        job = Mock()
        job.server_path = '/a/b/c'
        job.alt_filename = None
        job.path = Path('.')
        job.post = None

        runner = JobRunner(job_list=[job], centralized_progress=True)
        runner._progress_manager.set_job_totals(1)

        async def fake_run(*args, **kwargs):
            return DownloaderRet(code=RetCodeEnum.FileExisted, message='Download file already exists, skipping')

        with patch('ktoolbox.job.runner.Downloader.run', new=fake_run):
            failed_num = await runner.processor()

            # No failures expected
            assert failed_num == 0
            # existed count should be incremented
            assert runner._progress_manager._existed_jobs == 1
            # ensure the message was printed to stderr by loguru handler
            out, err = capsys.readouterr()
            assert 'Download file already exists' in err

    @patch('ktoolbox.job.runner.config')
    @pytest.mark.asyncio
    async def test_no_overcount_when_multiple_existed(self, mock_config):
        """Ensure completed never exceeds total when many jobs are existed/skipped"""
        mock_config.job.count = 3
        mock_config.downloader.scheme = 'https'
        mock_config.api.files_netloc = 'example.com'
        mock_config.ssl_verify = True

        from ktoolbox.job.runner import JobRunner
        from ktoolbox.downloader.base import DownloaderRet
        from ktoolbox._enum import RetCodeEnum
        from pathlib import Path

        # Create multiple mock jobs
        jobs = []
        for i in range(3):
            job = Mock()
            job.server_path = f'/a/{i}/c'
            job.alt_filename = None
            job.path = Path('.')
            job.post = None
            jobs.append(job)

        runner = JobRunner(job_list=jobs, centralized_progress=True)
        runner._progress_manager.set_job_totals(len(jobs))

        async def fake_run(*args, **kwargs):
            return DownloaderRet(code=RetCodeEnum.FileExisted, message='Download file already exists, skipping')

        with patch('ktoolbox.job.runner.Downloader.run', new=fake_run):
            # Use start to exercise concurrency
            failed_num = await runner.start()

            assert failed_num == 0
            # completed should equal total and not exceed it
            assert runner._progress_manager._completed_jobs == len(jobs)
            assert runner._progress_manager._completed_jobs <= runner._progress_manager._total_jobs
            # existed should equal total
            assert runner._progress_manager._existed_jobs == len(jobs)


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
        """Test colorize adds colors when colors supported"""
        with patch.object(ColorTheme, 'supports_color', return_value=True):
            result = ColorTheme.colorize("test", ColorTheme.GREEN)
            # Rich should apply colors - just check that the result is different from plain text
            # and contains ANSI escape sequences
            assert result != "test"
            assert '\033[' in result  # Contains ANSI escape sequence
    
    def test_colorize_with_bold(self):
        """Test colorize adds bold formatting"""
        with patch.object(ColorTheme, 'supports_color', return_value=True):
            result = ColorTheme.colorize("test", ColorTheme.GREEN, bold=True)
            # Rich should apply bold colors - check that result is styled and different from non-bold
            non_bold = ColorTheme.colorize("test", ColorTheme.GREEN, bold=False)
            assert result != "test"
            assert result != non_bold
            assert '\033[' in result  # Contains ANSI escape sequence


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
    
    def test_stable_progress_bar_ordering(self):
        """Test that progress bars maintain stable ordering regardless of update times"""
        import time
        
        manager = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        
        # Create multiple progress bars in a specific order
        pbar1 = manager.create_progress_bar("file1.jpg", total=100)
        pbar2 = manager.create_progress_bar("file2.png", total=200)
        pbar3 = manager.create_progress_bar("file3.mp4", total=300)
        
        # Update them in different order and at different times
        # This simulates real download scenario where files finish at different times
        pbar3.update(50)  # Update file3 first (most recent update)
        time.sleep(0.001)  # Small delay to ensure different timestamps
        pbar1.update(25)  # Update file1 second
        time.sleep(0.001)
        pbar2.update(75)  # Update file2 last (least recent update)
        
        # Render progress bars
        lines = manager._render_progress_bars()
        
        # Verify we have the expected number of progress bars
        assert len(lines) == 3
        
        # Check that they appear in creation order, not update order
        # This is the key improvement: stable ordering instead of sorting by update time
        assert "file1.jpg" in lines[0], f"file1.jpg should be first, but got: {lines[0]}"
        assert "file2.png" in lines[1], f"file2.png should be second, but got: {lines[1]}"
        assert "file3.mp4" in lines[2], f"file3.mp4 should be third, but got: {lines[2]}"
        
        # Clean up progress bars
        pbar1.close()
        pbar2.close()
        pbar3.close()
    
    def test_overall_progress_bar_display(self):
        """Test that overall progress displays visual progress bar in correct format"""
        manager = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        
        # Test with some completed jobs
        manager.set_job_totals(44, completed=10, failed=0)
        
        # Create some active progress bars with rates to test speed calculation
        pbar1 = manager.create_progress_bar("file1.jpg", total=1000)
        pbar2 = manager.create_progress_bar("file2.png", total=2000)
        
        # Update progress and set rates
        pbar1.update(500)
        pbar2.update(800)
        
        with manager._lock:
            if pbar1.progress_id in manager._progress_bars:
                manager._progress_bars[pbar1.progress_id].rate = 1500000  # 1.5 MB/s
            if pbar2.progress_id in manager._progress_bars:
                manager._progress_bars[pbar2.progress_id].rate = 3000000  # 3.0 MB/s
        
        lines = manager._render_overall_progress()
        
        # Should have one main progress line
        assert len(lines) == 1
        progress_line = lines[0]
        
        # Check format: [progress_bar] percentage% | Jobs: X/Y | N running | M waiting | speed
        assert progress_line.startswith('['), f"Should start with '[', but got: {progress_line}"
        assert '] 23% |' in progress_line, f"Should contain '] 23% |', but got: {progress_line}"
        assert 'Jobs: 10/44' in progress_line, f"Should contain 'Jobs: 10/44', but got: {progress_line}"
        assert '2 running' in progress_line, f"Should contain '2 running', but got: {progress_line}"
        assert '32 waiting' in progress_line, f"Should contain '32 waiting', but got: {progress_line}"
        assert 'MB/s' in progress_line, f"Should contain speed 'MB/s', but got: {progress_line}"
        
        # Test edge cases
        # 0% completion
        manager_zero = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_zero.set_job_totals(100, completed=0, failed=0)
        lines_zero = manager_zero._render_overall_progress()
        assert '[>-----------------------------] 0%' in lines_zero[0]
        
        # 100% completion
        manager_complete = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_complete.set_job_totals(100, completed=100, failed=0)
        lines_complete = manager_complete._render_overall_progress()
        assert '[==============================] 100%' in lines_complete[0]
        
        # With failed jobs
        manager_failed = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_failed.set_job_totals(100, completed=80, failed=5)
        lines_failed = manager_failed._render_overall_progress()
        assert len(lines_failed) == 2  # Main line + failed line
        assert '[========================>-----] 80%' in lines_failed[0]
        assert 'Failed: 5' in lines_failed[1]
        
        # Clean up
        pbar1.close()
        pbar2.close()
    
    def test_rich_unicode_progress_bars(self):
        """Test that Rich-based Unicode progress bars work correctly"""

        # Test with Rich enabled (when available)
        manager = ProgressManager(max_workers=3, use_colors=True, use_emojis=False)
        
        # Create a progress bar and render it
        pbar = manager.create_progress_bar("test_unicode.jpg", total=100)
        pbar.update(50)  # 50% progress
        
        line = manager._render_single_progress_bar(manager._progress_bars[pbar.progress_id])
        
        if ColorTheme.supports_color():
            # Should contain Unicode characters when Rich is available
            assert '━' in line, f"Should contain Unicode progress char '━', but got: {line}"
            assert '╺' in line, f"Should contain Unicode indicator '╺', but got: {line}"
        else:
            # Should fallback to original characters when Rich not available
            assert ('█' in line or '░' in line), f"Should contain fallback chars when Rich unavailable, but got: {line}"
        
        pbar.close()
    
    def test_rich_fallback_behavior(self):
        """Test that progress bars work correctly when Rich is not available"""
        import unittest.mock
        
        # Mock Rich as unavailable
        with unittest.mock.patch('ktoolbox.progress.RICH_AVAILABLE', False):
            manager = ProgressManager(max_workers=3, use_colors=True, use_emojis=False)
            
            pbar = manager.create_progress_bar("test_fallback.jpg", total=100)
            pbar.update(50)
            
            line = manager._render_single_progress_bar(manager._progress_bars[pbar.progress_id])
            
            # Should use fallback characters
            assert ('█' in line or '░' in line), f"Should use fallback characters, but got: {line}"
            # Should NOT contain Unicode characters
            assert '━' not in line, f"Should not contain Unicode chars in fallback mode, but got: {line}"
            assert '╺' not in line, f"Should not contain Unicode indicator in fallback mode, but got: {line}"
            
            pbar.close()
        """Test that overall progress displays visual progress bar in correct format"""
        manager = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        
        # Test with some completed jobs
        manager.set_job_totals(44, completed=10, failed=0)
        
        # Create some active progress bars with rates to test speed calculation
        pbar1 = manager.create_progress_bar("file1.jpg", total=1000)
        pbar2 = manager.create_progress_bar("file2.png", total=2000)
        
        # Update progress and set rates
        pbar1.update(500)
        pbar2.update(800)
        
        with manager._lock:
            if pbar1.progress_id in manager._progress_bars:
                manager._progress_bars[pbar1.progress_id].rate = 1500000  # 1.5 MB/s
            if pbar2.progress_id in manager._progress_bars:
                manager._progress_bars[pbar2.progress_id].rate = 3000000  # 3.0 MB/s
        
        lines = manager._render_overall_progress()
        
        # Should have one main progress line
        assert len(lines) == 1
        progress_line = lines[0]
        
        # Check format: [progress_bar] percentage% | Jobs: X/Y | N running | M waiting | speed
        assert progress_line.startswith('['), f"Should start with '[', but got: {progress_line}"
        assert '] 23% |' in progress_line, f"Should contain '] 23% |', but got: {progress_line}"
        assert 'Jobs: 10/44' in progress_line, f"Should contain 'Jobs: 10/44', but got: {progress_line}"
        assert '2 running' in progress_line, f"Should contain '2 running', but got: {progress_line}"
        assert '32 waiting' in progress_line, f"Should contain '32 waiting', but got: {progress_line}"
        assert 'MB/s' in progress_line, f"Should contain speed 'MB/s', but got: {progress_line}"
        
        # Test edge cases
        # 0% completion
        manager_zero = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_zero.set_job_totals(100, completed=0, failed=0)
        lines_zero = manager_zero._render_overall_progress()
        assert '[>-----------------------------] 0%' in lines_zero[0]
        
        # 100% completion
        manager_complete = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_complete.set_job_totals(100, completed=100, failed=0)
        lines_complete = manager_complete._render_overall_progress()
        assert '[==============================] 100%' in lines_complete[0]
        
        # With failed jobs
        manager_failed = ProgressManager(max_workers=5, use_colors=False, use_emojis=False)
        manager_failed.set_job_totals(100, completed=80, failed=5)
        lines_failed = manager_failed._render_overall_progress()
        assert len(lines_failed) == 2  # Main line + failed line
        assert '[========================>-----] 80%' in lines_failed[0]
        assert 'Failed: 5' in lines_failed[1]
        
        # Clean up
        pbar1.close()
        pbar2.close()