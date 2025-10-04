#!/usr/bin/env python3
"""
Test HTTP API communication between client_interface and session_manager
"""

import asyncio
import requests
import time
import sys

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful:")
            print(f"  Service: {data.get('service')}")
            print(f"  Status: {data.get('status')}")
            print(f"  ZMQ Connected: {data.get('details', {}).get('zmq_client_connected')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_plugins():
    """Test plugins endpoint"""
    try:
        response = requests.get("http://localhost:8080/api/plugins/available", timeout=10)
        if response.status_code == 200:
            data = response.json()
            plugins = data.get("plugins", [])
            print(f"✅ Plugins API successful: {len(plugins)} plugins available")
            return True
        else:
            print(f"❌ Plugins API failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Plugins API error: {e}")
        return False

def test_session_health():
    """Test session manager health via client interface"""
    try:
        response = requests.get("http://localhost:8080/api/session/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Session health check successful:")
            print(f"  Response: {data}")
            return True
        else:
            print(f"❌ Session health failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Session health error: {e}")
        return False

def main():
    """Main test function"""
    print("Testing communication between client_interface and session_manager...")
    print()

    # Wait a bit for services to be ready
    time.sleep(2)

    success_count = 0
    total_tests = 3

    if test_health():
        success_count += 1

    if test_plugins():
        success_count += 1

    if test_session_health():
        success_count += 1

    print()
    print(f"Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All communication tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())