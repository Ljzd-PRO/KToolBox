# WebUI Command

The `webui` command launches a Streamlit-based web interface for KToolBox, providing a remote graphical interface for all CLI functionality.

## Usage

```bash
ktoolbox webui
```

This will start a Streamlit server on `http://localhost:8501` with the KToolBox Web UI.

## Features

### 1. Sync Creator
- **Input Methods**: URL or Service + Creator ID
- **Parameters**: Download path, time ranges, keywords, offset/length controls
- **Features**: Save creator indices, mix posts, keyword filtering
- **Concurrency Control**: Prevents multiple sync operations running simultaneously

### 2. Download Post  
- **Input Methods**: URL or Service + Creator + Post ID
- **Parameters**: Revision ID support, download path, post data dumping
- **Features**: Single post/revision downloading
- **Concurrency Control**: Prevents multiple download operations running simultaneously

### 3. Other Commands
- **Version Display**: Shows KToolBox version
- **Site Version**: Fetches current Kemono site version
- **Config Editor**: Info about terminal config editor
- **Environment Generation**: Creates and displays example .env configuration with download capability

### 4. Status & Progress Monitoring
- **Real-time Status**: Shows current operation status
- **Job Statistics**: Waiting, processing, and completed job counts
- **Progress Tracking**: Visual progress bars and percentage completion
- **Operation Logs**: Recent activity logs with timestamps
- **Auto-refresh**: Optional 5-second auto-refresh capability

## State Management

The WebUI includes sophisticated state management to ensure reliable operation:

- **Concurrent Operation Prevention**: Only one sync_creator or download_post can run at a time
- **Operation Cancellation**: Users can cancel running operations
- **Progress Tracking**: Real-time updates from JobRunner and Downloader classes
- **Error Handling**: Comprehensive error catching and user feedback
- **Log Management**: Maintains last 100 log entries with timestamps

## Installation

The WebUI requires Streamlit as an optional dependency:

```bash
# Install with streamlit support
pip install ktoolbox[streamlit]

# Or if using pipx
pipx install ktoolbox[streamlit] --force
```

## Architecture

- **Frontend**: Streamlit-based reactive web interface
- **Backend**: Async task execution in separate threads
- **State**: Session-based state management using Streamlit's session state
- **Integration**: Direct integration with existing KToolBox CLI commands
- **Navigation**: Sidebar-based section navigation with quick status display

## Security Notes

- The web interface runs on localhost by default
- No authentication is built-in (intended for local use)
- All operations use the same permissions as the user running the command

## Browser Compatibility

The WebUI works with any modern web browser and automatically adapts to different screen sizes.