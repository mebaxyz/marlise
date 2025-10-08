#!/usr/bin/env python3
"""Test script for the integrated proxy functionality"""

import requests
import time
import subprocess
import signal
import os
import sys
from threading import Thread

def test_proxy_functionality():
    """Test that the integrated proxy works correctly"""
    
    print("🧪 Testing integrated Tornado proxy functionality...")
    
    # Test template serving
    try:
        response = requests.get('http://localhost:8888/', timeout=5)
        if response.status_code == 200:
            print("✅ Template serving: OK")
        else:
            print(f"❌ Template serving failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Template serving error: {e}")
    
    # Test API proxy (this will fail if FastAPI is not running, but should show proxy attempt)
    try:
        response = requests.get('http://localhost:8888/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ API proxy: OK (FastAPI responding)")
        elif response.status_code == 502:
            print("⚠️ API proxy: Working (502 = FastAPI not running, proxy is working)")
        else:
            print(f"❓ API proxy: Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API proxy error: {e}")
    
    # Test static file serving
    try:
        response = requests.get('http://localhost:8888/css/dashboard.css', timeout=5)
        if response.status_code == 200:
            print("✅ Static file serving: OK")
        else:
            print(f"❌ Static file serving: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Static file serving error: {e}")
    
    # Test WebSocket proxy endpoint (should return method not allowed for GET)
    try:
        response = requests.get('http://localhost:8888/websocket', timeout=5)
        if response.status_code == 405:  # Method not allowed for WebSocket endpoint
            print("✅ WebSocket proxy endpoint: OK (405 expected for GET)")
        else:
            print(f"❓ WebSocket proxy: Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ WebSocket proxy error: {e}")

def start_test_server():
    """Start the template server for testing"""
    print("🚀 Starting template server for testing...")
    
    # Change to the web_client_original directory
    os.chdir('/home/nicolas/project/marlise/client-interface/web_client_original')
    
    # Start the server
    process = subprocess.Popen([sys.executable, 'template_server.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    return process

if __name__ == '__main__':
    server_process = None
    
    try:
        # Start test server
        server_process = start_test_server()
        
        # Run tests
        test_proxy_functionality()
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    
    finally:
        # Clean up
        if server_process:
            print("🧹 Stopping test server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
        print("✅ Test completed")