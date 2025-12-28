"""
Centralized Progress Management for KToolBox

This module provides a centralized progress display system that prevents
multiple concurrent progress bars from interfering with each other.
Inspired by rclone's progress display approach with enhanced visual effects.
"""

import asyncio
import os
import sys
import threading
import time
from typing import Dict, List, Optional, TextIO
from dataclasses import dataclass, field

from tqdm import tqdm as std_tqdm
try:
    from rich.console import Console
    from rich.text import Text
    from rich.style import Style as RichStyle
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

__all__ = ["ProgressManager", "ManagedTqdm", "ColorTheme", "setup_logger_for_progress", "create_managed_tqdm_class"]

# Global reference to active progress manager for logger integration
_active_progress_manager: Optional['ProgressManager'] = None


def setup_logger_for_progress(progress_manager: 'ProgressManager' = None):
    """Setup logger to work with progress manager"""
    global _active_progress_manager
    _active_progress_manager = progress_manager


class ProgressAwareHandler:
    """Custom loguru handler that works with progress manager"""

    def __init__(self, original_handler):
        self.original_handler = original_handler

    def write(self, message):
        global _active_progress_manager
        if _active_progress_manager and _active_progress_manager._running:
            # Temporarily clear progress display
            _active_progress_manager.temporary_clear_for_log()
            self.original_handler.write(message)
            # Small delay to ensure message is visible
            time.sleep(0.05)
            # Restore progress display
            _active_progress_manager.restore_display()
        else:
            self.original_handler.write(message)

    def flush(self):
        if hasattr(self.original_handler, 'flush'):
            self.original_handler.flush()


class ColorTheme:
    """Rich-based color themes and styles for progress display"""

    # Rich console for color support detection and rendering
    _console = Console() if RICH_AVAILABLE else None

    # ANSI Color codes (fallback when Rich not available)
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Basic colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'

    # Rich style mappings
    if RICH_AVAILABLE:
        RICH_STYLES = {
            RED: "red",
            GREEN: "green",
            YELLOW: "yellow",
            BLUE: "blue", 
            MAGENTA: "magenta",
            CYAN: "cyan",
            WHITE: "white",
            BRIGHT_RED: "bright_red",
            BRIGHT_GREEN: "bright_green",
            BRIGHT_YELLOW: "bright_yellow",
            BRIGHT_BLUE: "bright_blue",
            BRIGHT_MAGENTA: "bright_magenta",
            BRIGHT_CYAN: "bright_cyan",
            BRIGHT_WHITE: "bright_white",
        }
    else:
        RICH_STYLES = {}

    # Emojis
    DOWNLOAD = "📥"
    COMPLETED = "✅"
    FAILED = "❌"
    RUNNING = "🔄"
    WAITING = "⏳"
    SPEED = "⚡"
    ROCKET = "🚀"

    # Animation frames for spinner
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    @classmethod
    def colorize(cls, text: str, color: str, bold: bool = False) -> str:
        """Apply color to text with optional bold using Rich when available"""
        if not cls.supports_color():
            return text
        
        if RICH_AVAILABLE:
            # Use Rich for more robust color support
            rich_color = cls.RICH_STYLES.get(color, color)
            style = f"bold {rich_color}" if bold else rich_color
            
            # Create a Text object and render it to get the styled string
            from rich.text import Text
            from rich.console import Console
            
            text_obj = Text(text, style=style)
            # Create a temporary console that forces color output for testing
            console = Console(force_terminal=True, width=1000)
            with console.capture() as capture:
                console.print(text_obj, end="")
            return capture.get()
        else:
            # Fallback to ANSI codes
            prefix = cls.BOLD + color if bold else color
            return f"{prefix}{text}{cls.RESET}"

    @classmethod
    def supports_color(cls) -> bool:
        """Check if terminal supports color using Rich when available"""
        if RICH_AVAILABLE and cls._console:
            # Rich handles color support detection better
            return cls._console.is_terminal and not cls._console.options.legacy_windows
        else:
            # Fallback to manual detection
            return (
                hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
                not sys.platform.startswith('win') or 'ANSICON' in os.environ
            )


# Animation state for spinners
_animation_state = {'frame': 0, 'last_update': 0.0}


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
    # Tracks the last state timestamp that was actually rendered.
    # Used to avoid advancing animation frames or forcing redraws
    # when nothing meaningful has changed.
    _last_render_seen: float = 0.0
    finished: bool = False
    failed: bool = False
    paused: bool = False


class ProgressManager:
    """
    Centralized progress manager that coordinates multiple progress bars
    in a fixed terminal display area with enhanced visual effects.
    """

    def __init__(self, max_workers: int = 5, file: Optional[TextIO] = None,
                 use_colors: bool = True, use_emojis: bool = True,
                 update_interval: float = 0.1):
        """
        Initialize the progress manager.
        
        :param max_workers: Maximum number of concurrent progress bars to display
        :param file: Output stream (defaults to sys.stdout)
        :param use_colors: Enable color output
        :param use_emojis: Enable emoji indicators
        """
        self.max_workers = max_workers
        self.file = file or sys.stdout
        self.use_colors = use_colors and ColorTheme.supports_color()
        self.use_emojis = use_emojis
        self._progress_bars: Dict[str, ProgressState] = {}
        self._display_order: List[str] = []
        self._lock = threading.RLock()
        self._display_task: Optional[asyncio.Task] = None
        self._running = False
        self._total_jobs = 0
        self._completed_jobs = 0
        self._failed_jobs = 0
        self._existed_jobs = 0

        # Terminal control
        self._lines_written = 0
        self._last_display_time = 0
        # Update interval (seconds). When downloads change, refresh at most
        # once per `update_interval`. Default is 1.0s to avoid excessive redraws.
        self._update_interval = float(update_interval)

        # Display deduplication
        self._last_display_content = ""

    def set_job_totals(self, total: int, completed: int = 0, failed: int = 0, existed: int = 0):
        """Set the total number of jobs for overall progress tracking"""
        with self._lock:
            self._total_jobs = total
            self._completed_jobs = completed
            self._failed_jobs = failed
            self._existed_jobs = existed

    def update_job_progress(self, completed: int = None, failed: int = None, existed: int = None):
        """Update overall job progress"""
        with self._lock:
            if completed is not None:
                self._completed_jobs = completed
            if failed is not None:
                self._failed_jobs = failed
            if existed is not None:
                self._existed_jobs = existed

    def increment_existed(self, n: int = 1) -> int:
        """Atomically increment the existed count by n and return the new value"""
        with self._lock:
            self._existed_jobs += n
            return self._existed_jobs

    def create_progress_bar(self, desc: str, total: Optional[int] = None,
                          unit: str = "B", unit_scale: bool = True) -> 'ManagedTqdm':
        """Create a new managed progress bar"""
        # Don't create progress state here - let ManagedTqdm do it with proper unique ID
        return ManagedTqdm(desc=desc, total=total, unit=unit, unit_scale=unit_scale, manager=self)

    def update_progress(self, progress_id: str, current: int, desc: str = None, failed: bool = False):
        """Update progress for a specific progress bar"""
        with self._lock:
            if progress_id in self._progress_bars:
                state = self._progress_bars[progress_id]
                state.current = current
                state.failed = failed
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

    def finish_progress(self, progress_id: str, failed: bool = False):
        """Mark a progress bar as finished"""
        with self._lock:
            if progress_id in self._progress_bars:
                self._progress_bars[progress_id].finished = True
                self._progress_bars[progress_id].failed = failed
                # Remove finished progress bar immediately in sync context
                # to avoid coroutine warnings
                try:
                    loop = asyncio.get_running_loop()
                    # Only create task if we're in an async context with a running loop
                    loop.create_task(self._remove_finished_after_delay(progress_id))
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
            # Set as active progress manager for logger integration
            setup_logger_for_progress(self)

    def stop_display(self):
        """Stop the progress display loop"""
        if self._running:
            self._running = False
            # Clear display area and show cursor
            self._clear_display()
            self.file.write('\033[?25h\n')
            self.file.flush()
            # Remove from logger integration
            setup_logger_for_progress(None)

    def _clear_display(self):
        """Clear the current display area"""
        if self._lines_written > 0 and self.file.isatty():
            # Move cursor up to the start of our display area
            self.file.write(f'\033[{self._lines_written}A')
            # Clear each line and move to next
            for _ in range(self._lines_written):
                self.file.write('\033[2K\033[1B')  # Clear line and move down
            # Move cursor back to start of display area
            self.file.write(f'\033[{self._lines_written}A')
            self.file.flush()
            self._lines_written = 0

    def temporary_clear_for_log(self, log_message: str = None):
        """Temporarily clear display to allow log output"""
        if self._running and self.file.isatty():
            self._clear_display()
            # Reset last display content so we redraw after logging
            self._last_display_content = ""
            if log_message:
                self.file.write(log_message + '\n')
                self.file.flush()

    def restore_display(self):
        """Restore display after log output"""
        if self._running and self.file.isatty():
            # Force immediate display update
            self.update_display()

    @staticmethod
    def _format_size(size: Optional[int], unit_scale: bool = True) -> str:
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

    def _format_rate(self, rate: Optional[float]) -> str:
        """Format a rate value"""
        if rate is None:
            return "?/s"
        return f"{self._format_size(int(rate))}/s"

    def _render_overall_progress(self) -> List[str]:
        """Render the overall job progress with colors and emojis, including visual progress bar"""
        lines = []

        if self._total_jobs > 0:
            running = len([p for p in self._progress_bars.values() if not p.finished])
            waiting = max(0, self._total_jobs - self._completed_jobs - self._failed_jobs - running)

            progress_pct = (self._completed_jobs / self._total_jobs) * 100 if self._total_jobs > 0 else 0
            progress_ratio = self._completed_jobs / self._total_jobs if self._total_jobs > 0 else 0

            # Determine overall status emoji and color
            if self.use_emojis:
                if running > 0:
                    status_emoji = f"{ColorTheme.RUNNING} "
                elif self._failed_jobs > 0:
                    status_emoji = f"{ColorTheme.FAILED} "
                else:
                    status_emoji = f"{ColorTheme.COMPLETED} "
            else:
                status_emoji = ""

            # Create visual progress bar
            bar_width = 30
            filled = int(bar_width * progress_ratio)
            
            if self.use_colors:
                if progress_pct >= 100:
                    bar_filled = ColorTheme.colorize('=' * filled, ColorTheme.BRIGHT_GREEN)
                    bar_empty = ColorTheme.colorize('-' * (bar_width - filled), ColorTheme.GREEN)
                elif progress_pct >= 75:
                    bar_filled = ColorTheme.colorize('=' * filled, ColorTheme.BRIGHT_CYAN)
                    bar_empty = ColorTheme.colorize('>' + '-' * (bar_width - filled), ColorTheme.CYAN)
                else:
                    bar_filled = ColorTheme.colorize('=' * filled, ColorTheme.BRIGHT_YELLOW)
                    bar_empty = ColorTheme.colorize('>' + '-' * (bar_width - filled), ColorTheme.YELLOW)
                
                bar_display = bar_filled + bar_empty
            else:
                bar_filled = '=' * filled
                bar_empty = '-' * (bar_width - filled)
                if filled < bar_width and progress_pct < 100:
                    bar_display = bar_filled + '>' + bar_empty[1:] if filled > 0 else '>' + bar_empty[1:]
                else:
                    bar_display = bar_filled + bar_empty

            # Color the progress percentage
            if self.use_colors:
                if progress_pct >= 100:
                    pct_colored = ColorTheme.colorize(f"{progress_pct:.0f}%", ColorTheme.BRIGHT_GREEN, bold=True)
                elif progress_pct >= 75:
                    pct_colored = ColorTheme.colorize(f"{progress_pct:.0f}%", ColorTheme.BRIGHT_CYAN, bold=True)
                elif progress_pct >= 50:
                    pct_colored = ColorTheme.colorize(f"{progress_pct:.0f}%", ColorTheme.BRIGHT_YELLOW, bold=True)
                else:
                    pct_colored = ColorTheme.colorize(f"{progress_pct:.0f}%", ColorTheme.BRIGHT_WHITE, bold=True)
            else:
                pct_colored = f"{progress_pct:.0f}%"

            # Color status numbers
            if self.use_colors:
                completed_colored = ColorTheme.colorize(str(self._completed_jobs), ColorTheme.BRIGHT_GREEN)
                total_colored = ColorTheme.colorize(str(self._total_jobs), ColorTheme.BRIGHT_WHITE)
                running_colored = ColorTheme.colorize(str(running), ColorTheme.BRIGHT_CYAN)
                waiting_colored = ColorTheme.colorize(str(waiting), ColorTheme.BRIGHT_YELLOW)
                existed_colored = ColorTheme.colorize(str(self._existed_jobs), ColorTheme.BRIGHT_WHITE)
            else:
                completed_colored = str(self._completed_jobs)
                total_colored = str(self._total_jobs)
                running_colored = str(running)
                waiting_colored = str(waiting)
                existed_colored = str(self._existed_jobs)

            # Calculate overall download speed from active progress bars
            total_rate = 0
            active_count = 0
            for state in self._progress_bars.values():
                if not state.finished and state.rate and state.rate > 0:
                    total_rate += state.rate
                    active_count += 1
            
            # Format overall speed
            if total_rate > 0:
                speed_str = self._format_rate(total_rate)
                if self.use_colors:
                    speed_str = ColorTheme.colorize(speed_str, ColorTheme.BRIGHT_MAGENTA)
            else:
                speed_str = ""

            # Build the main progress line in the requested format
            # [================>----------------] 23% | Jobs: 10/44 | 4 running | 30 waiting | 4.5 MB/s
            line_parts = []
            
            if status_emoji:  # Only add emoji if it's not empty
                line_parts.append(status_emoji)
            
            line_parts.extend([
                f"[{bar_display}]",
                pct_colored,
                f"| Jobs: {completed_colored}/{total_colored}",
                f"| {running_colored} running",
                f"| {waiting_colored} waiting",
                f"| {existed_colored} existed"
            ])
            
            if speed_str:
                line_parts.append(f"| {speed_str}")
            
            line = " ".join(line_parts)
            lines.append(line)

            # Show failed jobs on a separate line if any
            if self._failed_jobs > 0:
                failed_emoji = f"{ColorTheme.FAILED} " if self.use_emojis else ""
                if self.use_colors:
                    failed_colored = ColorTheme.colorize(str(self._failed_jobs), ColorTheme.BRIGHT_RED, bold=True)
                else:
                    failed_colored = str(self._failed_jobs)
                lines.append(f"{failed_emoji}Failed: {failed_colored}")

        return lines

    def _render_progress_bars(self) -> List[str]:
        """Render individual progress bars"""
        lines = []

        # Show only active progress bars in stable order (up to max_workers)
        # Use display_order to maintain consistent positioning instead of sorting by update time
        active_progress = []
        for progress_id in self._display_order:
            if (progress_id in self._progress_bars and 
                not self._progress_bars[progress_id].finished):
                active_progress.append((progress_id, self._progress_bars[progress_id]))

        for progress_id, state in active_progress[:self.max_workers]:
            line = self._render_single_progress_bar(state)
            lines.append(line)

        return lines

    def _render_single_progress_bar(self, state: ProgressState) -> str:
        """Render a single progress bar with colors and animations"""
        # Progress bar width
        bar_width = 30

        # Determine status emoji
        if self.use_emojis:
            if state.failed:
                status_emoji = ColorTheme.FAILED
            elif state.finished:
                status_emoji = ColorTheme.COMPLETED
            elif state.paused:
                status_emoji = ColorTheme.WAITING
            else:
                # Animated spinner for active downloads
                # Advance spinner only when this progress state's content changed
                # since the last render to avoid continuous terminal refreshes
                # caused solely by animation frames.
                current_time = time.time()
                last_seen = getattr(state, '_last_render_seen', 0.0)
                if state.last_update != last_seen:
                    _animation_state['frame'] = (_animation_state['frame'] + 1) % len(ColorTheme.SPINNER_FRAMES)
                    _animation_state['last_update'] = current_time
                    state._last_render_seen = state.last_update
                status_emoji = ColorTheme.SPINNER_FRAMES[_animation_state['frame']]
        else:
            status_emoji = ""

        if state.total is not None and state.total > 0:
            progress = min(state.current / state.total, 1.0)
            filled = int(bar_width * progress)

            # Create colored progress bar with Unicode characters when Rich is available
            if self.use_colors and RICH_AVAILABLE:
                # Use Unicode characters: ━━━╺━━━━━━━ with Rich colors
                if state.failed:
                    # Red for failed
                    if filled > 0:
                        if filled < bar_width:
                            bar_filled = ColorTheme.colorize('━' * (filled - 1), 'bright_red')
                            bar_empty = ColorTheme.colorize('╺' + '━' * (bar_width - filled), 'bright_black')
                        else:
                            bar_filled = ColorTheme.colorize('━' * filled, 'bright_red')
                            bar_empty = ''
                    else:
                        bar_filled = ''
                        bar_empty = ColorTheme.colorize('━' * bar_width, 'bright_black')
                elif state.finished:
                    # Green for completed
                    bar_filled = ColorTheme.colorize('━' * filled, 'bright_green')
                    bar_empty = ColorTheme.colorize('━' * (bar_width - filled), 'bright_black')
                else:
                    # Pink/Magenta for in progress
                    if filled > 0:
                        if filled < bar_width:
                            bar_filled = ColorTheme.colorize('━' * (filled - 1), 'bright_magenta')
                            bar_empty = ColorTheme.colorize('╺' + '━' * (bar_width - filled), 'bright_black')
                        else:
                            bar_filled = ColorTheme.colorize('━' * filled, 'bright_magenta')
                            bar_empty = ''
                    else:
                        bar_filled = ''
                        bar_empty = ColorTheme.colorize('━' * bar_width, 'bright_black')
                bar = bar_filled + bar_empty
            elif self.use_colors:
                # Fallback to original characters with ANSI colors when Rich not available
                if state.failed:
                    # Red for failed
                    bar_filled = ColorTheme.colorize('█' * filled, ColorTheme.BRIGHT_RED)
                    bar_empty = ColorTheme.colorize('░' * (bar_width - filled), ColorTheme.RED)
                elif state.finished:
                    # Green for completed
                    bar_filled = ColorTheme.colorize('█' * filled, ColorTheme.BRIGHT_GREEN)
                    bar_empty = ColorTheme.colorize('░' * (bar_width - filled), ColorTheme.GREEN)
                else:
                    # Cyan for in progress
                    bar_filled = ColorTheme.colorize('█' * filled, ColorTheme.BRIGHT_CYAN)
                    bar_empty = ColorTheme.colorize('░' * (bar_width - filled), ColorTheme.CYAN)
                bar = bar_filled + bar_empty
            else:
                # No colors - use original characters
                bar = '█' * filled + '░' * (bar_width - filled)

            # Color the percentage
            percentage_val = progress * 100
            if self.use_colors:
                if percentage_val >= 100:
                    percentage = ColorTheme.colorize(f"{percentage_val:5.1f}%", ColorTheme.BRIGHT_GREEN, bold=True)
                elif percentage_val >= 75:
                    percentage = ColorTheme.colorize(f"{percentage_val:5.1f}%", ColorTheme.BRIGHT_CYAN)
                else:
                    percentage = ColorTheme.colorize(f"{percentage_val:5.1f}%", ColorTheme.BRIGHT_WHITE)
            else:
                percentage = f"{percentage_val:5.1f}%"
        else:
            # Indeterminate progress with animated bar
            if self.use_colors and RICH_AVAILABLE:
                # Moving progress indicator with Unicode characters
                pos = _animation_state['frame'] % bar_width
                bar_chars = ['━'] * bar_width
                for i in range(max(0, pos-2), min(bar_width, pos+3)):
                    bar_chars[i] = '━'
                bar_chars[pos] = '╺'  # Current position indicator
                bar = ColorTheme.colorize(''.join(bar_chars), 'bright_yellow')
            elif self.use_colors:
                # Fallback to original characters
                pos = _animation_state['frame'] % bar_width
                bar_chars = ['░'] * bar_width
                for i in range(max(0, pos-2), min(bar_width, pos+3)):
                    bar_chars[i] = '█'
                bar = ColorTheme.colorize(''.join(bar_chars), ColorTheme.BRIGHT_YELLOW)
            else:
                bar = '█' * 3 + '░' * (bar_width - 3)
            percentage = ColorTheme.colorize("  ?  %", ColorTheme.BRIGHT_YELLOW) if self.use_colors else "  ?  %"

        # Format sizes with color
        current_str = self._format_size(state.current, state.unit_scale)
        total_str = self._format_size(state.total, state.unit_scale) if state.total else "?"

        if self.use_colors:
            current_str = ColorTheme.colorize(current_str, ColorTheme.BRIGHT_WHITE, bold=True)
            total_str = ColorTheme.colorize(total_str, ColorTheme.BRIGHT_WHITE)

        # Format rate with speed emoji
        rate_str = self._format_rate(state.rate)
        if self.use_colors and state.rate and state.rate > 0:
            rate_str = ColorTheme.colorize(rate_str, ColorTheme.BRIGHT_MAGENTA)

        if self.use_emojis and state.rate and state.rate > 0:
            rate_str = f"{ColorTheme.SPEED} {rate_str}"

        # Truncate description if too long and add color
        desc = state.desc
        if len(desc) > 25:
            desc = desc[:22] + "..."

        if self.use_colors:
            if state.failed:
                desc = ColorTheme.colorize(desc, ColorTheme.BRIGHT_RED)
            elif state.finished:
                desc = ColorTheme.colorize(desc, ColorTheme.BRIGHT_GREEN)
            else:
                desc = ColorTheme.colorize(desc, ColorTheme.BRIGHT_CYAN)

        # Add emoji prefix
        if self.use_emojis:
            desc = f"{status_emoji} {desc}"

        return f"{desc:30} |{bar}| {current_str}/{total_str} {percentage} {rate_str}"

    def update_display(self):
        """Update the terminal display"""
        if not self._running or not self.file.isatty():
            return

        current_time = time.time()
        if current_time - self._last_display_time < self._update_interval:
            return

        self._last_display_time = current_time

        with self._lock:
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

            # Write to terminal only if we have content and it's different from last display
            if lines:
                # Remove trailing empty lines
                while lines and lines[-1] == "":
                    lines.pop()

                if lines:  # Check again after removing empty lines
                    display_content = '\n'.join(lines)

                    # Only update if content has changed
                    if display_content != self._last_display_content:
                        # Clear previous display
                        self._clear_display()

                        output = display_content + '\n'
                        self.file.write(output)
                        self.file.flush()
                        self._lines_written = len(lines)
                        self._last_display_content = display_content


class ManagedTqdm:
    """
    A tqdm-compatible progress bar that works with ProgressManager.
    This class mimics the tqdm interface but delegates to ProgressManager.
    """

    def __init__(self, desc=None, total=None, initial=0, disable=False,
                 unit="it", unit_scale=False, manager=None, **kwargs):
        self._failed = False
        self._paused = False
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
        return None

    def set_description(self, desc: str):
        """Set the description of the progress bar"""
        if self._fallback:
            return self._fallback.set_description(desc)

        self._desc = desc
        self.manager.update_progress(self.progress_id, self._current, desc)
        return None

    def close(self):
        """Close/finish the progress bar"""
        if self._fallback:
            return self._fallback.close()

        if self.manager and self.progress_id:
            self.manager.finish_progress(self.progress_id, failed=getattr(self, '_failed', False))
        return None

    def __enter__(self):
        if self._fallback:
            return self._fallback.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fallback:
            return self._fallback.__exit__(exc_type, exc_val, exc_tb)
        self.close()
        return None

    def set_failed(self, failed: bool = True):
        """Mark the progress bar as failed"""
        if self._fallback:
            return  # Not supported in fallback mode

        self._failed = failed
        if self.manager and self.progress_id:
            self.manager.update_progress(self.progress_id, self._current, self._desc, failed=failed)

    def set_paused(self, paused: bool = True):
        """Mark the progress bar as paused"""
        if self._fallback:
            return  # Not supported in fallback mode

        self._paused = paused
        if self.manager and self.progress_id:
            with self.manager._lock:
                if self.progress_id in self.manager._progress_bars:
                    self.manager._progress_bars[self.progress_id].paused = paused

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
        except Exception:
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