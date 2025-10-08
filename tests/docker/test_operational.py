#!/usr/bin/env python3
"""
Simple test runner to verify the fully operational test platform
"""

import asyncio
import json
import time
import zmq
import zmq.asyncio
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mock_mod_host():
    """Test mock mod-host TCP connection"""
    print("🎵 Testing mock mod-host...")
    try:
        reader, writer = await asyncio.open_connection('localhost', 5555)
        writer.write(b"ping\n")
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
        print(f"✅ Mock mod-host response: {response.decode().strip()}")
        return True
    except Exception as e:
        print(f"❌ Mock mod-host error: {e}")
        return False

async def test_mock_modhost_bridge():
    """Test mock modhost-bridge ZMQ connection"""
    print("🌉 Testing mock modhost-bridge...")
    try:
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://localhost:6000')
        socket.setsockopt(zmq.RCVTIMEO, 5000)
        
        request = {
            'jsonrpc': '2.0',
            'method': 'get_jack_status',
            'id': 1
        }
        
        await socket.send_json(request)
        response = await socket.recv_json()
        socket.close()
        context.term()
        
        print(f"✅ Mock modhost-bridge response: {response}")
        return True
    except Exception as e:
        print(f"❌ Mock modhost-bridge error: {e}")
        return False

async def test_full_chain():
    """Test loading a plugin through the mock chain"""
    print("🔌 Testing full plugin loading chain...")
    try:
        # Test modhost-bridge plugin loading
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://localhost:6000')
        socket.setsockopt(zmq.RCVTIMEO, 10000)
        
        request = {
            'jsonrpc': '2.0', 
            'method': 'load_plugin',
            'params': {
                'uri': 'http://calf.sourceforge.net/plugins/Reverb'
            },
            'id': 1
        }
        
        await socket.send_json(request)
        response = await socket.recv_json()
        socket.close()
        context.term()
        
        if response.get('result', {}).get('success'):
            print(f"✅ Full chain plugin load: Success, instance_id: {response['result']['instance_id']}")
            return True
        else:
            print(f"❌ Full chain plugin load failed: {response}")
            return False
    except Exception as e:
        print(f"❌ Full chain error: {e}")
        return False

def check_process_status():
    """Check which processes are running"""
    print("🔍 Checking process status...")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        services = ['mock_mod_host', 'mock_modhost_bridge', 'jackd', 'session_manager', 'uvicorn']
        for service in services:
            if service in processes:
                print(f"✅ {service}: Running")
            else:
                print(f"❌ {service}: Not found")
                
    except Exception as e:
        print(f"❌ Process check error: {e}")

def check_ports():
    """Check which ports are listening"""
    print("🌐 Checking port status...")
    ports = [5555, 6000, 5718, 8080]
    
    for port in ports:
        try:
            result = subprocess.run(['netstat', '-tuln'], capture_output=True, text=True)
            if f':{port}' in result.stdout:
                print(f"✅ Port {port}: Open")
            else:
                print(f"❌ Port {port}: Not listening")
        except Exception as e:
            print(f"❌ Port check error: {e}")

async def main():
    """Run all operational tests"""
    print("🧪 Testing Fully Operational Test Platform")
    print("==========================================")
    
    # Basic status checks
    check_process_status()
    check_ports()
    
    # Wait a bit for services to be ready
    print("⏳ Waiting for services to stabilize...")
    await asyncio.sleep(5)
    
    # Test each component
    tests = [
        test_mock_mod_host(),
        test_mock_modhost_bridge(),
        test_full_chain()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Summary
    success_count = sum(1 for r in results if r is True)
    total_count = len(results)
    
    print(f"\n📊 Test Results: {success_count}/{total_count} passed")
    
    if success_count == total_count:
        print("🎉 FULLY OPERATIONAL TEST PLATFORM READY!")
        print("✅ All mock services working correctly")
        print("✅ ZeroMQ communication operational") 
        print("✅ Plugin loading chain functional")
        print("\n📋 Ready for full integration tests:")
        print("    ./run_integration_tests.sh")
        return True
    else:
        print("⚠️  Some issues found, but core functionality available")
        return False

if __name__ == "__main__":
    asyncio.run(main())