"""Web UI server runner"""

import uvicorn
from loguru import logger
from ..configuration import config
from .app import create_app

def run_webui():
    """Run the Web UI server"""
    logger.info(f"Starting KToolBox Web UI server on {config.webui.host}:{config.webui.port}")
    logger.info(f"Access the Web UI at: http://{config.webui.host}:{config.webui.port}")
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=config.webui.host,
        port=config.webui.port,
        log_level="info",
        access_log=config.webui.debug
    )