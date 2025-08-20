# Centralized Progress Display

KToolBox now features a centralized progress display system that prevents progress bar chaos during concurrent downloads. This addresses the issue where multiple progress bars from concurrent downloads would interfere with each other in the terminal.

## Features

- **Fixed Display Area**: Progress bars stay in designated terminal area and update in place
- **Overall Job Progress**: Shows total completion progress for all download jobs
- **Individual File Progress**: Shows progress for currently active downloads
- **Clean Organization**: Similar to rclone's progress display approach
- **Backward Compatibility**: Can be disabled to use traditional tqdm behavior

## How It Works

The centralized progress system consists of:

1. **ProgressManager**: Coordinates all progress displays in a fixed terminal area
2. **ManagedTqdm**: A tqdm-compatible wrapper that works with ProgressManager
3. **JobRunner Integration**: Automatically uses centralized progress by default

## Display Layout

```
Jobs: 3/10 completed (30.0%), 2 running, 5 waiting

image1.jpg               |████████░░░░░░░░░░░░░░░░░░░░░░| 256KB/1.0MB  25.0% 512KB/s
video.mp4                |███░░░░░░░░░░░░░░░░░░░░░░░░░░░| 1.5MB/10MB   15.0% 2.1MB/s
```

- **Top Line**: Overall job completion status
- **Below**: Individual file progress bars for active downloads

## Configuration

### Enable/Disable Centralized Progress

```python
from ktoolbox.job.runner import JobRunner

# Centralized progress enabled (default)
runner = JobRunner(progress=True, centralized_progress=True)

# Traditional tqdm behavior  
runner = JobRunner(progress=True, centralized_progress=False)

# Disable progress entirely
runner = JobRunner(progress=False)
```

### Custom Progress Display

```python
from ktoolbox.progress import ProgressManager, create_managed_tqdm_class

# Create custom progress manager
manager = ProgressManager(max_workers=5)  # Show up to 5 concurrent progress bars
tqdm_class = create_managed_tqdm_class(manager)

runner = JobRunner(tqdm_class=tqdm_class, centralized_progress=True)
```

## Benefits

1. **No More Chaos**: Progress bars no longer jump around or overlap
2. **Better Visibility**: Clear overall progress and individual file status
3. **Performance**: Reduced terminal output and smoother updates
4. **Professional Look**: Clean, organized display similar to professional tools like rclone

## Implementation Details

- Uses terminal control codes to update display in place
- Thread-safe progress coordination
- Graceful fallback to standard tqdm when needed
- Minimal performance overhead
- Full compatibility with existing tqdm interface

## Backward Compatibility

Existing code continues to work unchanged:

```python
# This still works exactly as before
runner = JobRunner(job_list=jobs, progress=True)

# But now gets organized progress display by default
```

To get the old behavior:

```python
runner = JobRunner(job_list=jobs, progress=True, centralized_progress=False)
```