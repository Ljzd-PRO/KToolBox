"""
Streamlit Web UI for KToolBox
"""
import asyncio
import sys
import threading
import time
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


class WebUIState:
    """Manages state for long-running operations"""
    
    def __init__(self):
        self.sync_creator_running = False
        self.download_post_running = False
        self.current_job_runner: Optional[JobRunner] = None
        self.job_stats: Dict[str, Any] = {}
        self.logs: List[str] = []
        
    def is_busy(self) -> bool:
        """Check if any long-running operation is active"""
        return self.sync_creator_running or self.download_post_running
        
    def start_sync_creator(self):
        """Mark sync_creator as running"""
        self.sync_creator_running = True
        
    def stop_sync_creator(self):
        """Mark sync_creator as finished"""
        self.sync_creator_running = False
        
    def start_download_post(self):
        """Mark download_post as running"""
        self.download_post_running = True
        
    def stop_download_post(self):
        """Mark download_post as finished"""
        self.download_post_running = False
        
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
            
    def add_log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]


def get_webui_state() -> WebUIState:
    """Get or create WebUI state from Streamlit session state"""
    if 'webui_state' not in st.session_state:
        st.session_state.webui_state = WebUIState()
    return st.session_state.webui_state


async def run_sync_creator_async(
    state: WebUIState,
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
    """Run sync_creator command asynchronously"""
    try:
        state.start_sync_creator()
        state.add_log(f"Starting sync_creator for {'URL: ' + url if url else f'Service: {service}, Creator: {creator_id}'}")
        
        # Convert keywords from string to tuple if provided
        keywords_tuple = tuple(keywords.split(',')) if keywords and keywords.strip() else None
        keywords_exclude_tuple = tuple(keywords_exclude.split(',')) if keywords_exclude and keywords_exclude.strip() else None
        
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
        
        if result is None:
            state.add_log("sync_creator completed successfully")
        else:
            state.add_log(f"sync_creator failed: {result}")
            
    except Exception as e:
        state.add_log(f"sync_creator error: {str(e)}")
        logger.error(f"WebUI sync_creator error: {e}")
    finally:
        state.stop_sync_creator()


async def run_download_post_async(
    state: WebUIState,
    url: str = None,
    service: str = None,
    creator_id: str = None,
    post_id: str = None,
    revision_id: str = None,
    path: str = ".",
    dump_post_data: bool = True
):
    """Run download_post command asynchronously"""
    try:
        state.start_download_post()
        state.add_log(f"Starting download_post for {'URL: ' + url if url else f'Service: {service}, Creator: {creator_id}, Post: {post_id}'}")
        
        result = await KToolBoxCli.download_post(
            url=url,
            service=service,
            creator_id=creator_id,
            post_id=post_id,
            revision_id=revision_id,
            path=Path(path),
            dump_post_data=dump_post_data
        )
        
        if result is None:
            state.add_log("download_post completed successfully")
        else:
            state.add_log(f"download_post failed: {result}")
            
    except Exception as e:
        state.add_log(f"download_post error: {str(e)}")
        logger.error(f"WebUI download_post error: {e}")
    finally:
        state.stop_download_post()


def run_async_command(coro):
    """Run async command in a thread"""
    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    
    thread = threading.Thread(target=target, daemon=True)
    thread.start()


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
            # TODO: Implement cancellation
            st.warning("Cancellation not yet implemented")
    else:
        # Validate inputs
        valid_input = False
        if input_method == "URL" and url:
            valid_input = True
        elif input_method == "Service + Creator ID" and service and creator_id:
            valid_input = True
        
        if st.button("Start Sync Creator", disabled=not valid_input or state.is_busy(), key="start_sync", type="primary"):
            coro = run_sync_creator_async(
                state=state,
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
            run_async_command(coro)
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
            # TODO: Implement cancellation
            st.warning("Cancellation not yet implemented")
    else:
        # Validate inputs
        valid_input = False
        if input_method == "URL" and url:
            valid_input = True
        elif input_method == "Service + Creator + Post" and service and creator_id and post_id:
            valid_input = True
        
        if st.button("Start Download Post", disabled=not valid_input or state.is_busy(), key="start_download", type="primary"):
            coro = run_download_post_async(
                state=state,
                url=url,
                service=service,
                creator_id=creator_id,
                post_id=post_id,
                revision_id=revision_id,
                path=path,
                dump_post_data=dump_post_data
            )
            run_async_command(coro)
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
        
        if st.button("Show Site Version", key="show_site_version"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                site_version = loop.run_until_complete(KToolBoxCli.site_version())
                st.success(f"Site Version: {site_version}")
                loop.close()
            except Exception as e:
                st.error(f"Error getting site version: {e}")
    
    with col2:
        if st.button("Launch Config Editor", key="launch_config_editor"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(KToolBoxCli.config_editor())
                st.success("Config editor launched (check terminal)")
                loop.close()
            except Exception as e:
                st.error(f"Error launching config editor: {e}")
                
        if st.button("Generate Example .env", key="generate_env"):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(KToolBoxCli.example_env())
                st.success("Example .env file generated")
                loop.close()
            except Exception as e:
                st.error(f"Error generating .env: {e}")
    
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
            state.logs = []
            st.rerun()


def main():
    """Main Streamlit app"""
    if st is None:
        st.error("Streamlit is not installed. Please install it with: pip install ktoolbox[streamlit]")
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