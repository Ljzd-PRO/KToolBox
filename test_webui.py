#!/usr/bin/env python3
"""Simple test script to verify Web UI APIs work correctly"""

import asyncio
import httpx
import time
import subprocess
import sys
from pathlib import Path

def start_webui_server():
    """Start the webui server in background"""
    return subprocess.Popen([
        sys.executable, "-m", "ktoolbox", "webui"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

async def test_apis():
    """Test all Web UI APIs"""
    base_url = "http://127.0.0.1:8890"
    auth = ("admin", "admin")
    
    async with httpx.AsyncClient() as client:
        # Test authentication
        print("Testing authentication...")
        response = await client.get(f"{base_url}/auth/status", auth=auth)
        assert response.status_code == 200, f"Auth failed: {response.status_code}"
        data = response.json()
        assert data["authenticated"] is True
        print("✓ Authentication works")
        
        # Test version API
        print("Testing version API...")
        response = await client.get(f"{base_url}/api/version", auth=auth)
        assert response.status_code == 200, f"Version API failed: {response.status_code}"
        version_data = response.json()
        assert "version" in version_data
        print(f"✓ Version API works: {version_data['version']}")
        
        # Test configuration API
        print("Testing configuration API...")
        response = await client.get(f"{base_url}/api/config", auth=auth)
        assert response.status_code == 200, f"Config API failed: {response.status_code}"
        config_data = response.json()
        assert "api" in config_data and "webui" in config_data
        print("✓ Configuration API works")
        
        # Test tasks API
        print("Testing tasks API...")
        response = await client.get(f"{base_url}/api/tasks", auth=auth)
        assert response.status_code == 200, f"Tasks API failed: {response.status_code}"
        tasks_data = response.json()
        assert "tasks" in tasks_data
        print("✓ Tasks API works")
        
        print("\n🎉 All API tests passed!")

async def main():
    """Main test function"""
    print("Starting KToolBox Web UI API tests...")
    
    # Start the server
    print("Starting Web UI server...")
    server_process = start_webui_server()
    
    try:
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Run tests
        await test_apis()
        
    finally:
        # Clean up
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())