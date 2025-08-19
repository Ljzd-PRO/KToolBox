"""
Streamlit Web UI for KToolBox
"""
import asyncio
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import streamlit as st
except ImportError:
    st = None

from loguru import logger

# Now import ktoolbox modules
try:
    from ktoolbox.cli import KToolBoxCli
    from ktoolbox.job.runner import JobRunner
    from ktoolbox.utils import generate_msg
except ImportError as e:
    # Graceful fallback when ktoolbox modules are not available
    logger.error(f"Failed to import ktoolbox modules: {e}")
    KToolBoxCli = None
    JobRunner = None
    generate_msg = None


# Persistent state file location
STATE_FILE = Path.home() / ".ktoolbox_webui_state.json"

# Global thread tracking
_active_threads: Dict[str, threading.Thread] = {}
_cancellation_events: Dict[str, threading.Event] = {}


class PersistentWebUIState:
    """Manages persistent state for long-running operations that survives browser refresh"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.sync_creator_running = False
        self.download_post_running = False
        self.current_job_runner: Optional[JobRunner] = None
        self.job_stats: Dict[str, Any] = {}
        self.logs: List[str] = []
        self.sync_creator_session_id: Optional[str] = None
        self.download_post_session_id: Optional[str] = None
        self._show_recovery_message = False
        self._load_state()
        
    def _get_state_data(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            "sync_creator_running": self.sync_creator_running,
            "download_post_running": self.download_post_running,
            "job_stats": self.job_stats,
            "logs": self.logs[-100:],  # Keep only last 100 logs
            "sync_creator_session_id": self.sync_creator_session_id,
            "download_post_session_id": self.download_post_session_id,
            "last_update": datetime.now().isoformat()
        }
        
    def _save_state(self):
        """Save state to persistent file"""
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self._get_state_data(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save WebUI state: {e}")
            
    def _load_state(self):
        """Load state from persistent file"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    
                # Check if state is recent (within last hour)
                last_update = datetime.fromisoformat(data.get("last_update", "2000-01-01"))
                if (datetime.now() - last_update).total_seconds() > 3600:
                    # State is too old, reset to clean state
                    self._clear_old_state()
                    return
                    
                self.sync_creator_running = data.get("sync_creator_running", False)
                self.download_post_running = data.get("download_post_running", False)
                self.job_stats = data.get("job_stats", {})
                self.logs = data.get("logs", [])
                self.sync_creator_session_id = data.get("sync_creator_session_id")
                self.download_post_session_id = data.get("download_post_session_id")
                
                # Verify if reported running operations are actually still running
                self._verify_running_operations()
                
        except Exception as e:
            logger.warning(f"Failed to load WebUI state: {e}")
            self._clear_old_state()
    
    def _clear_old_state(self):
        """Clear old state and reset to defaults"""
        self.sync_creator_running = False
        self.download_post_running = False
        self.job_stats = {}
        self.logs = []
        self.sync_creator_session_id = None
        self.download_post_session_id = None
        self._show_recovery_message = False
        try:
            if STATE_FILE.exists():
                STATE_FILE.unlink()
        except Exception:
            pass
            
    def _verify_running_operations(self):
        """Verify if operations marked as running are actually still running"""
        global _active_threads
        
        recovery_needed = False
        
        # Check sync_creator
        if self.sync_creator_running and self.sync_creator_session_id:
            thread = _active_threads.get(self.sync_creator_session_id)
            if not thread or not thread.is_alive():
                self.sync_creator_running = False
                self.sync_creator_session_id = None
                self.add_log("Sync creator operation was interrupted (possibly by browser refresh)")
                recovery_needed = True
                
        # Check download_post 
        if self.download_post_running and self.download_post_session_id:
            thread = _active_threads.get(self.download_post_session_id)
            if not thread or not thread.is_alive():
                self.download_post_running = False
                self.download_post_session_id = None
                self.add_log("Download post operation was interrupted (possibly by browser refresh)")
                recovery_needed = True
                
        if recovery_needed:
            self._show_recovery_message = True
                
        self._save_state()
        
    def is_busy(self) -> bool:
        """Check if any long-running operation is active"""
        self._verify_running_operations()
        return self.sync_creator_running or self.download_post_running
        
    def start_sync_creator(self, session_id: str):
        """Mark sync_creator as running with session tracking"""
        self.sync_creator_running = True
        self.sync_creator_session_id = session_id
        self._save_state()
        
    def stop_sync_creator(self):
        """Mark sync_creator as finished"""
        if self.sync_creator_session_id:
            _active_threads.pop(self.sync_creator_session_id, None)
            _cancellation_events.pop(self.sync_creator_session_id, None)
        self.sync_creator_running = False
        self.sync_creator_session_id = None
        self._save_state()
        
    def start_download_post(self, session_id: str):
        """Mark download_post as running with session tracking"""
        self.download_post_running = True
        self.download_post_session_id = session_id
        self._save_state()
        
    def stop_download_post(self):
        """Mark download_post as finished"""
        if self.download_post_session_id:
            _active_threads.pop(self.download_post_session_id, None)
            _cancellation_events.pop(self.download_post_session_id, None)
        self.download_post_running = False
        self.download_post_session_id = None
        self._save_state()
        
    def cancel_sync_creator(self):
        """Cancel sync_creator operation"""
        if self.sync_creator_session_id:
            # Signal cancellation
            event = _cancellation_events.get(self.sync_creator_session_id)
            if event:
                event.set()
            self.add_log("Sync creator operation cancelled by user")
        self.stop_sync_creator()
        
    def cancel_download_post(self):
        """Cancel download_post operation"""
        if self.download_post_session_id:
            # Signal cancellation
            event = _cancellation_events.get(self.download_post_session_id)
            if event:
                event.set()
            self.add_log("Download post operation cancelled by user")
        self.stop_download_post()
        
    def update_job_stats(self, job_runner: JobRunner):
        """Update job statistics from JobRunner"""
        if job_runner:
            self.current_job_runner = job_runner
            self.job_stats = {
                "waiting": job_runner.waiting_size,
                "processing": job_runner.processing_size,
                "done": job_runner.done_size,
                "finished": job_runner.finished
            }
            self._save_state()
            
    def add_log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        self._save_state()
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        self._save_state()


def get_webui_state() -> PersistentWebUIState:
    """Get or create WebUI state from Streamlit session state with persistence"""
    if 'webui_state' not in st.session_state:
        st.session_state.webui_state = PersistentWebUIState()
    return st.session_state.webui_state


async def run_sync_creator_async(
    state: PersistentWebUIState,
    session_id: str,
    cancellation_event: threading.Event,
    url: str = None,
    service: str = None,
    creator_id: str = None,
    path: str = ".",
    save_creator_indices: bool = False,
    mix_posts: bool = None,
    start_time: str = None,
    end_time: str = None,
    offset: int = 0,
    length: int = None,
    keywords: str = None,
    keywords_exclude: str = None
):
    """Run sync_creator command asynchronously with cancellation support"""
    try:
        state.start_sync_creator(session_id)
        state.add_log(f"Starting sync_creator for {'URL: ' + url if url else f'Service: {service}, Creator: {creator_id}'}")
        
        # Convert keywords from string to tuple if provided
        keywords_tuple = tuple(keywords.split(',')) if keywords and keywords.strip() else None
        keywords_exclude_tuple = tuple(keywords_exclude.split(',')) if keywords_exclude and keywords_exclude.strip() else None
        
        # Check for cancellation before starting
        if cancellation_event.is_set():
            state.add_log("sync_creator cancelled before starting")
            return
        
        result = await KToolBoxCli.sync_creator(
            url=url,
            service=service,
            creator_id=creator_id,
            path=Path(path),
            save_creator_indices=save_creator_indices,
            mix_posts=mix_posts,
            start_time=start_time,
            end_time=end_time,
            offset=offset,
            length=length,
            keywords=keywords_tuple,
            keywords_exclude=keywords_exclude_tuple
        )
        
        # Check for cancellation after completion
        if cancellation_event.is_set():
            state.add_log("sync_creator was cancelled during execution")
            return
        
        if result is None:
            state.add_log("sync_creator completed successfully")
        else:
            state.add_log(f"sync_creator failed: {result}")
            
    except asyncio.CancelledError:
        state.add_log("sync_creator was cancelled")
    except Exception as e:
        state.add_log(f"sync_creator error: {str(e)}")
        logger.error(f"WebUI sync_creator error: {e}")
    finally:
        state.stop_sync_creator()


async def run_download_post_async(
    state: PersistentWebUIState,
    session_id: str,
    cancellation_event: threading.Event,
    url: str = None,
    service: str = None,
    creator_id: str = None,
    post_id: str = None,
    revision_id: str = None,
    path: str = ".",
    dump_post_data: bool = True
):
    """Run download_post command asynchronously with cancellation support"""
    try:
        state.start_download_post(session_id)
        state.add_log(f"Starting download_post for {'URL: ' + url if url else f'Service: {service}, Creator: {creator_id}, Post: {post_id}'}")
        
        # Check for cancellation before starting
        if cancellation_event.is_set():
            state.add_log("download_post cancelled before starting")
            return
        
        result = await KToolBoxCli.download_post(
            url=url,
            service=service,
            creator_id=creator_id,
            post_id=post_id,
            revision_id=revision_id,
            path=Path(path),
            dump_post_data=dump_post_data
        )
        
        # Check for cancellation after completion
        if cancellation_event.is_set():
            state.add_log("download_post was cancelled during execution")
            return
        
        if result is None:
            state.add_log("download_post completed successfully")
        else:
            state.add_log(f"download_post failed: {result}")
            
    except asyncio.CancelledError:
        state.add_log("download_post was cancelled")
    except Exception as e:
        state.add_log(f"download_post error: {str(e)}")
        logger.error(f"WebUI download_post error: {e}")
    finally:
        state.stop_download_post()


def run_async_command(coro, state: PersistentWebUIState, operation: str):
    """Run async command in a thread with proper session tracking"""
    session_id = str(uuid.uuid4())
    cancellation_event = threading.Event()
    
    # Store the cancellation event for later use
    _cancellation_events[session_id] = cancellation_event
    
    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        except asyncio.CancelledError:
            state.add_log(f"{operation} was cancelled")
        except Exception as e:
            state.add_log(f"{operation} error: {str(e)}")
            logger.error(f"WebUI {operation} error: {e}")
        finally:
            loop.close()
            # Clean up session tracking
            _active_threads.pop(session_id, None)
            _cancellation_events.pop(session_id, None)
    
    thread = threading.Thread(target=target, daemon=True, name=f"ktoolbox-{operation}-{session_id[:8]}")
    _active_threads[session_id] = thread
    thread.start()
    
    return session_id


def render_sync_creator_section():
    """Render sync_creator command section"""
    state = get_webui_state()
    
    st.header("📥 Sync Creator")
    st.write("Download all posts from a creator")
    
    # Input method selection
    input_method = st.radio("Input method:", ["URL", "Service + Creator ID"], key="sync_method")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if input_method == "URL":
            url = st.text_input("Creator URL:", key="sync_url", placeholder="https://kemono.su/fanbox/user/12345")
            service = None
            creator_id = None
        else:
            url = None
            service = st.selectbox("Service:", ["fanbox", "patreon", "discord", "fantia", "subscribestar", "gumroad", "dlsite"], key="sync_service")
            creator_id = st.text_input("Creator ID:", key="sync_creator_id", placeholder="12345")
        
        path = st.text_input("Download path:", value=".", key="sync_path")
        save_creator_indices = st.checkbox("Save creator indices", key="sync_save_indices")
        mix_posts = st.checkbox("Mix posts", key="sync_mix_posts")
    
    with col2:
        start_time = st.date_input("Start time (optional):", value=None, key="sync_start_time")
        end_time = st.date_input("End time (optional):", value=None, key="sync_end_time")
        offset = st.number_input("Offset:", min_value=0, value=0, key="sync_offset")
        length = st.number_input("Length (optional, 0 = all):", min_value=0, value=0, key="sync_length")
        keywords = st.text_input("Keywords (comma-separated):", key="sync_keywords", placeholder="keyword1,keyword2")
        keywords_exclude = st.text_input("Exclude keywords (comma-separated):", key="sync_keywords_exclude", placeholder="exclude1,exclude2")
    
    # Convert inputs
    start_time_str = start_time.strftime("%Y-%m-%d") if start_time else None
    end_time_str = end_time.strftime("%Y-%m-%d") if end_time else None
    length_val = length if length > 0 else None
    
    # Validation and submission
    if state.sync_creator_running:
        st.warning("🔄 Sync creator is currently running. Please wait for it to complete.")
        if st.button("Cancel Sync Creator", key="cancel_sync", type="secondary"):
            state.cancel_sync_creator()
            st.success("Sync creator operation cancelled!")
            st.rerun()
    else:
        # Validate inputs
        valid_input = False
        if input_method == "URL" and url:
            valid_input = True
        elif input_method == "Service + Creator ID" and service and creator_id:
            valid_input = True
        
        if st.button("Start Sync Creator", disabled=not valid_input or state.is_busy(), key="start_sync", type="primary"):
            session_id = str(uuid.uuid4())
            cancellation_event = threading.Event()
            
            coro = run_sync_creator_async(
                state=state,
                session_id=session_id,
                cancellation_event=cancellation_event,
                url=url,
                service=service,
                creator_id=creator_id,
                path=path,
                save_creator_indices=save_creator_indices,
                mix_posts=mix_posts if mix_posts else None,
                start_time=start_time_str,
                end_time=end_time_str,
                offset=offset,
                length=length_val,
                keywords=keywords,
                keywords_exclude=keywords_exclude
            )
            run_async_command(coro, state, "sync_creator")
            st.success("Sync creator started!")
            st.rerun()


def render_download_post_section():
    """Render download_post command section"""
    state = get_webui_state()
    
    st.header("📄 Download Post")
    st.write("Download a specific post or revision")
    
    # Input method selection
    input_method = st.radio("Input method:", ["URL", "Service + Creator + Post"], key="download_method")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if input_method == "URL":
            url = st.text_input("Post URL:", key="download_url", placeholder="https://kemono.su/fanbox/user/12345/post/67890")
            service = None
            creator_id = None
            post_id = None
        else:
            url = None
            service = st.selectbox("Service:", ["fanbox", "patreon", "discord", "fantia", "subscribestar", "gumroad", "dlsite"], key="download_service")
            creator_id = st.text_input("Creator ID:", key="download_creator_id", placeholder="12345")
            post_id = st.text_input("Post ID:", key="download_post_id", placeholder="67890")
    
    with col2:
        revision_id = st.text_input("Revision ID (optional):", key="download_revision_id", placeholder="Leave empty for latest")
        path = st.text_input("Download path:", value=".", key="download_path")
        dump_post_data = st.checkbox("Dump post data", value=True, key="download_dump_data")
    
    # Convert inputs
    revision_id = revision_id if revision_id.strip() else None
    
    # Validation and submission
    if state.download_post_running:
        st.warning("🔄 Download post is currently running. Please wait for it to complete.")
        if st.button("Cancel Download Post", key="cancel_download", type="secondary"):
            state.cancel_download_post()
            st.success("Download post operation cancelled!")
            st.rerun()
    else:
        # Validate inputs
        valid_input = False
        if input_method == "URL" and url:
            valid_input = True
        elif input_method == "Service + Creator + Post" and service and creator_id and post_id:
            valid_input = True
        
        if st.button("Start Download Post", disabled=not valid_input or state.is_busy(), key="start_download", type="primary"):
            session_id = str(uuid.uuid4())
            cancellation_event = threading.Event()
            
            coro = run_download_post_async(
                state=state,
                session_id=session_id,
                cancellation_event=cancellation_event,
                url=url,
                service=service,
                creator_id=creator_id,
                post_id=post_id,
                revision_id=revision_id,
                path=path,
                dump_post_data=dump_post_data
            )
            run_async_command(coro, state, "download_post")
            st.success("Download post started!")
            st.rerun()


def render_other_commands_section():
    """Render other CLI commands section"""
    st.header("🔧 Other Commands")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Show Version", key="show_version"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                version = loop.run_until_complete(KToolBoxCli.version())
                st.success(f"KToolBox Version: {version}")
                loop.close()
            except Exception as e:
                st.error(f"Error getting version: {e}")
                logger.error(f"WebUI version command error: {e}")
        
        if st.button("Show Site Version", key="show_site_version"):
            try:
                with st.spinner("Fetching site version..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    site_version = loop.run_until_complete(KToolBoxCli.site_version())
                    if site_version:
                        st.success(f"Site Version: {site_version}")
                    else:
                        st.warning("Could not fetch site version")
                    loop.close()
            except Exception as e:
                st.error(f"Error getting site version: {e}")
                logger.error(f"WebUI site_version command error: {e}")
    
    with col2:
        if st.button("Launch Config Editor", key="launch_config_editor"):
            try:
                # Since config editor is a terminal app, just show info message
                st.info("Config editor is a terminal application. To use it, run: `ktoolbox config-editor` in your terminal.")
            except Exception as e:
                st.error(f"Error with config editor: {e}")
                logger.error(f"WebUI config_editor command error: {e}")
                
        if st.button("Generate Example .env", key="generate_env"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Capture the output instead of printing to stdout
                import io
                import contextlib
                
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    loop.run_until_complete(KToolBoxCli.example_env())
                
                env_content = f.getvalue()
                if env_content:
                    st.success("Example .env content generated:")
                    st.code(env_content, language="bash")
                    st.download_button(
                        label="Download .env file",
                        data=env_content,
                        file_name="example.env",
                        mime="text/plain"
                    )
                else:
                    st.warning("No .env content generated")
                loop.close()
            except Exception as e:
                st.error(f"Error generating .env: {e}")
                logger.error(f"WebUI example_env command error: {e}")
    
    with col3:
        st.write("**Search Commands**")
        st.info("Search creator and search creator post commands can be added in future versions")


def render_status_section():
    """Render status and progress section"""
    state = get_webui_state()
    
    st.header("📊 Status & Progress")
    
    # Current operations status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if state.sync_creator_running:
            st.metric("Sync Creator", "🔄 Running", delta="Active")
        else:
            st.metric("Sync Creator", "✅ Ready", delta="Idle")
    
    with col2:
        if state.download_post_running:
            st.metric("Download Post", "🔄 Running", delta="Active")
        else:
            st.metric("Download Post", "✅ Ready", delta="Idle")
    
    with col3:
        busy_status = "🔄 Busy" if state.is_busy() else "✅ Ready"
        st.metric("System Status", busy_status, delta="")
    
    # Job statistics
    if state.job_stats:
        st.subheader("Job Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Waiting", state.job_stats.get("waiting", 0))
        with col2:
            st.metric("Processing", state.job_stats.get("processing", 0))
        with col3:
            st.metric("Done", state.job_stats.get("done", 0))
        with col4:
            total = state.job_stats.get("waiting", 0) + state.job_stats.get("processing", 0) + state.job_stats.get("done", 0)
            if total > 0:
                progress = (state.job_stats.get("done", 0) / total) * 100
                st.metric("Progress", f"{progress:.1f}%")
    
    # Logs section
    if state.logs:
        st.subheader("Recent Logs")
        log_text = "\n".join(state.logs[-10:])  # Show last 10 logs
        st.text_area("", value=log_text, height=200, key="logs_display")
        
        if st.button("Clear Logs", key="clear_logs"):
            state.clear_logs()
            st.rerun()


def main():
    """Main Streamlit app"""
    if st is None:
        print("Streamlit is not installed. Please install it with: pip install ktoolbox[streamlit]")
        return
    
    if KToolBoxCli is None:
        st.error("KToolBox modules are not available. Please ensure ktoolbox is properly installed.")
        return
    
    st.set_page_config(
        page_title="KToolBox Web UI",
        page_icon="🧰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🧰 KToolBox Web UI")
    st.write("Remote interface for KToolBox CLI commands")
    
    # Get state early to check for recovery scenarios
    state = get_webui_state()
    
    # Show recovery message if operations were interrupted
    if hasattr(state, '_show_recovery_message'):
        if state._show_recovery_message:
            st.warning("⚠️ Some operations may have been interrupted by a browser refresh. Check the Status & Progress section for details.")
            state._show_recovery_message = False
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        selected_section = st.radio(
            "Select section:",
            ["Sync Creator", "Download Post", "Other Commands", "Status & Progress"],
            key="navigation"
        )
        
        # Auto-refresh option
        auto_refresh = st.checkbox("Auto-refresh (5s)", key="auto_refresh")
        if auto_refresh:
            time.sleep(5)
            st.rerun()
    
    # Main content area
    if selected_section == "Sync Creator":
        render_sync_creator_section()
    elif selected_section == "Download Post":
        render_download_post_section()
    elif selected_section == "Other Commands":
        render_other_commands_section()
    elif selected_section == "Status & Progress":
        render_status_section()
    
    # Always show status in the sidebar
    with st.sidebar:
        st.header("Quick Status")
        state = get_webui_state()
        
        if state.sync_creator_running:
            st.warning("🔄 Sync Creator Running")
        if state.download_post_running:
            st.warning("🔄 Download Post Running")
        if not state.is_busy():
            st.success("✅ All systems ready")
        
        if state.job_stats:
            st.write("**Job Progress:**")
            total = state.job_stats.get("waiting", 0) + state.job_stats.get("processing", 0) + state.job_stats.get("done", 0)
            if total > 0:
                progress = state.job_stats.get("done", 0) / total
                st.progress(progress)
                st.caption(f"{state.job_stats.get('done', 0)}/{total} jobs completed")


if __name__ == "__main__":
    main()