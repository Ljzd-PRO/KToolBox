"""
Centralized Progress Management for KToolBox

This module provides a centralized progress display system that prevents
multiple concurrent progress bars from interfering with each other.
Inspired by rclone's progress display approach.
"""

import asyncio
import sys
import threading
import time
from typing import Dict, List, Optional, TextIO
from dataclasses import dataclass, field

from tqdm import tqdm as std_tqdm

__all__ = ["ProgressManager", "ManagedTqdm"]


@dataclass
class ProgressState:
    """Represents the state of a single progress bar"""
    desc: str = ""
    total: Optional[int] = None
    current: int = 0
    unit: str = "it"
    unit_scale: bool = False
    rate: Optional[float] = None
    last_update: float = field(default_factory=time.time)
    finished: bool = False


class ProgressManager:
    """
    Centralized progress manager that coordinates multiple progress bars
    in a fixed terminal display area.
    """
    
    def __init__(self, max_workers: int = 5, file: Optional[TextIO] = None):
        """
        Initialize the progress manager.
        
        :param max_workers: Maximum number of concurrent progress bars to display
        :param file: Output stream (defaults to sys.stdout)
        """
        self.max_workers = max_workers
        self.file = file or sys.stdout
        self._progress_bars: Dict[str, ProgressState] = {}
        self._display_order: List[str] = []
        self._lock = threading.RLock()
        self._display_task: Optional[asyncio.Task] = None
        self._running = False
        self._total_jobs = 0
        self._completed_jobs = 0
        self._failed_jobs = 0
        
        # Terminal control
        self._lines_written = 0
        self._last_display_time = 0
        self._update_interval = 0.1  # Update every 100ms
        
    def set_job_totals(self, total: int, completed: int = 0, failed: int = 0):
        """Set the total number of jobs for overall progress tracking"""
        with self._lock:
            self._total_jobs = total
            self._completed_jobs = completed
            self._failed_jobs = failed
    
    def update_job_progress(self, completed: int = None, failed: int = None):
        """Update overall job progress"""
        with self._lock:
            if completed is not None:
                self._completed_jobs = completed
            if failed is not None:
                self._failed_jobs = failed
    
    def create_progress_bar(self, desc: str, total: Optional[int] = None, 
                          unit: str = "B", unit_scale: bool = True) -> 'ManagedTqdm':
        """Create a new managed progress bar"""
        progress_id = f"{desc}_{id(desc)}"
        
        with self._lock:
            self._progress_bars[progress_id] = ProgressState(
                desc=desc, total=total, unit=unit, unit_scale=unit_scale
            )
            if progress_id not in self._display_order:
                self._display_order.append(progress_id)
        
        return ManagedTqdm(self, progress_id)
    
    def update_progress(self, progress_id: str, current: int, desc: str = None):
        """Update progress for a specific progress bar"""
        with self._lock:
            if progress_id in self._progress_bars:
                state = self._progress_bars[progress_id]
                state.current = current
                if desc:
                    state.desc = desc
                state.last_update = time.time()
                
                # Calculate rate
                if hasattr(state, '_last_current') and hasattr(state, '_last_time'):
                    time_diff = state.last_update - state._last_time
                    if time_diff > 0:
                        current_diff = current - state._last_current
                        state.rate = current_diff / time_diff
                
                state._last_current = current
                state._last_time = state.last_update
    
    def finish_progress(self, progress_id: str):
        """Mark a progress bar as finished"""
        with self._lock:
            if progress_id in self._progress_bars:
                self._progress_bars[progress_id].finished = True
                # Schedule removal after a short delay
                try:
                    # Only create task if we're in an async context
                    asyncio.create_task(self._remove_finished_after_delay(progress_id))
                except RuntimeError:
                    # No event loop running, remove immediately
                    if progress_id in self._progress_bars:
                        del self._progress_bars[progress_id]
                    if progress_id in self._display_order:
                        self._display_order.remove(progress_id)
    
    async def _remove_finished_after_delay(self, progress_id: str, delay: float = 1.0):
        """Remove a finished progress bar after a delay"""
        await asyncio.sleep(delay)
        with self._lock:
            if progress_id in self._progress_bars and self._progress_bars[progress_id].finished:
                del self._progress_bars[progress_id]
                if progress_id in self._display_order:
                    self._display_order.remove(progress_id)
    
    def start_display(self):
        """Start the progress display loop"""
        if not self._running and self.file.isatty():
            self._running = True
            # Hide cursor
            self.file.write('\033[?25l')
            self.file.flush()
    
    def stop_display(self):
        """Stop the progress display loop"""
        if self._running:
            self._running = False
            # Clear display area and show cursor
            self._clear_display()
            self.file.write('\033[?25h\n')
            self.file.flush()
    
    def _clear_display(self):
        """Clear the current display area"""
        if self._lines_written > 0:
            # Move cursor up and clear lines
            self.file.write(f'\033[{self._lines_written}A')
            for _ in range(self._lines_written):
                self.file.write('\033[2K\n')
            self.file.write(f'\033[{self._lines_written}A')
            self._lines_written = 0
    
    def _format_size(self, size: Optional[int], unit_scale: bool = True) -> str:
        """Format a size value with appropriate units"""
        if size is None:
            return "?"
        
        if not unit_scale:
            return str(size)
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size_float = float(size)
        unit_index = 0
        
        while size_float >= 1024 and unit_index < len(units) - 1:
            size_float /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{size}B"
        else:
            return f"{size_float:.1f}{units[unit_index]}"
    
    def _format_rate(self, rate: Optional[float], unit: str = "B") -> str:
        """Format a rate value"""
        if rate is None:
            return "?/s"
        return f"{self._format_size(int(rate))}/s"
    
    def _render_overall_progress(self) -> List[str]:
        """Render the overall job progress"""
        lines = []
        
        if self._total_jobs > 0:
            running = len([p for p in self._progress_bars.values() if not p.finished])
            waiting = max(0, self._total_jobs - self._completed_jobs - self._failed_jobs - running)
            
            progress_pct = (self._completed_jobs / self._total_jobs) * 100 if self._total_jobs > 0 else 0
            
            lines.append(f"Jobs: {self._completed_jobs}/{self._total_jobs} completed ({progress_pct:.1f}%), "
                        f"{running} running, {waiting} waiting")
            
            if self._failed_jobs > 0:
                lines.append(f"Failed: {self._failed_jobs}")
        
        return lines
    
    def _render_progress_bars(self) -> List[str]:
        """Render individual progress bars"""
        lines = []
        
        # Show only active progress bars (up to max_workers)
        active_progress = [
            (pid, state) for pid, state in self._progress_bars.items()
            if not state.finished
        ]
        
        # Sort by last update time (most recent first)
        active_progress.sort(key=lambda x: x[1].last_update, reverse=True)
        
        for progress_id, state in active_progress[:self.max_workers]:
            line = self._render_single_progress_bar(state)
            lines.append(line)
        
        return lines
    
    def _render_single_progress_bar(self, state: ProgressState) -> str:
        """Render a single progress bar"""
        # Progress bar width
        bar_width = 30
        
        if state.total is not None and state.total > 0:
            progress = min(state.current / state.total, 1.0)
            filled = int(bar_width * progress)
            bar = '█' * filled + '░' * (bar_width - filled)
            percentage = f"{progress * 100:5.1f}%"
        else:
            # Indeterminate progress
            bar = '█' * 3 + '░' * (bar_width - 3)
            percentage = "  ?  %"
        
        # Format sizes
        current_str = self._format_size(state.current, state.unit_scale)
        total_str = self._format_size(state.total, state.unit_scale) if state.total else "?"
        rate_str = self._format_rate(state.rate, state.unit)
        
        # Truncate description if too long
        desc = state.desc
        if len(desc) > 25:
            desc = desc[:22] + "..."
        
        return f"{desc:25} |{bar}| {current_str}/{total_str} {percentage} {rate_str}"
    
    def update_display(self):
        """Update the terminal display"""
        if not self._running or not self.file.isatty():
            return
        
        current_time = time.time()
        if current_time - self._last_display_time < self._update_interval:
            return
        
        self._last_display_time = current_time
        
        with self._lock:
            # Clear previous display
            self._clear_display()
            
            # Render new display
            lines = []
            
            # Overall progress
            overall_lines = self._render_overall_progress()
            if overall_lines:
                lines.extend(overall_lines)
                lines.append("")  # Separator
            
            # Individual progress bars
            progress_lines = self._render_progress_bars()
            lines.extend(progress_lines)
            
            # Write to terminal
            if lines:
                output = '\n'.join(lines) + '\n'
                self.file.write(output)
                self.file.flush()
                self._lines_written = len(lines)


class ManagedTqdm:
    """
    A tqdm-compatible progress bar that works with ProgressManager.
    This class mimics the tqdm interface but delegates to ProgressManager.
    """
    
    def __init__(self, desc=None, total=None, initial=0, disable=False, 
                 unit="it", unit_scale=False, manager=None, **kwargs):
        # If no manager provided or disabled, fall back to standard tqdm
        if manager is None or disable:
            self._fallback = std_tqdm(desc=desc, total=total, initial=initial, 
                                    disable=disable, unit=unit, unit_scale=unit_scale, **kwargs)
            self.manager = None
            self.progress_id = None
        else:
            self.manager = manager
            self._fallback = None
            self._current = initial
            self._total = total
            self._desc = desc or ""
            self._disable = disable
            self._unit = unit
            self._unit_scale = unit_scale
            
            # Create progress bar in manager
            self.progress_id = f"{desc}_{id(self)}"
            with self.manager._lock:
                self.manager._progress_bars[self.progress_id] = ProgressState(
                    desc=self._desc, total=total, current=initial, 
                    unit=unit, unit_scale=unit_scale
                )
                if self.progress_id not in self.manager._display_order:
                    self.manager._display_order.append(self.progress_id)
        
    def update(self, n: int = 1):
        """Update the progress bar by n units"""
        if self._fallback:
            return self._fallback.update(n)
            
        self._current += n
        self.manager.update_progress(self.progress_id, self._current, self._desc)
        self.manager.update_display()
    
    def set_description(self, desc: str):
        """Set the description of the progress bar"""
        if self._fallback:
            return self._fallback.set_description(desc)
            
        self._desc = desc
        self.manager.update_progress(self.progress_id, self._current, desc)
    
    def close(self):
        """Close/finish the progress bar"""
        if self._fallback:
            return self._fallback.close()
            
        if self.manager and self.progress_id:
            self.manager.finish_progress(self.progress_id)
    
    def __enter__(self):
        if self._fallback:
            return self._fallback.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fallback:
            return self._fallback.__exit__(exc_type, exc_val, exc_tb)
        self.close()
    
    # Properties to maintain compatibility with tqdm
    @property
    def total(self):
        if self._fallback:
            return self._fallback.total
        return self._total
    
    @total.setter
    def total(self, value):
        if self._fallback:
            self._fallback.total = value
        else:
            self._total = value
    
    @property
    def n(self):
        if self._fallback:
            return self._fallback.n
        return self._current
    
    @n.setter
    def n(self, value):
        if self._fallback:
            self._fallback.n = value
        else:
            self._current = value
            if self.manager:
                self.manager.update_progress(self.progress_id, self._current, self._desc)
                
    def __bool__(self):
        """For compatibility with tqdm boolean checks"""
        return True
        
    def __del__(self):
        """Cleanup when object is garbage collected"""
        try:
            self.close()
        except:
            pass


def create_managed_tqdm_class(progress_manager: ProgressManager):
    """
    Create a tqdm class factory that uses the given ProgressManager.
    This allows us to create a drop-in replacement for tqdm.
    """
    class ManagedTqdmClass(ManagedTqdm):
        def __init__(self, *args, **kwargs):
            kwargs['manager'] = progress_manager
            super().__init__(*args, **kwargs)
    
    return ManagedTqdmClass