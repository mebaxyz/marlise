#!/usr/bin/env python3
"""
Test ZeroMQ Communication

Simple test to verify direct ZeroMQ communication between services
without using the ServiceBus package.
"""

import asyncio
import logging
import sys
from zmq_service import ZMQService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_client():
    """Test ZeroMQ client functionality"""
    try:
        # Create a test client
        client = ZMQService("test_client")
        await client.start()
        
        logger.info("Test client started, attempting to call session_manager...")
        
        # Test calling the session manager
        try:
            result = await client.call("session_manager", "health_check", timeout=5.0)
            logger.info("Health check response: %s", result)
            
            # Test getting available plugins
            result = await client.call("session_manager", "get_available_plugins", timeout=10.0)
            if result and result.get("success"):
                plugins = result.get("plugins", [])
                logger.info("Available plugins: %s plugins found", len(plugins))
            else:
                logger.error("Failed to get plugins: %s", result)
                
        except Exception as e:
            logger.error("RPC call failed: %s", e)
        
        await client.stop()
        return True
        
    except Exception as e:
        logger.error("Test client failed: %s", e)
        return False


async def main():
    """Main test function"""
    logger.info("Starting ZeroMQ communication test...")
    
    success = await test_client()
    
    if success:
        logger.info("✅ ZeroMQ communication test completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ ZeroMQ communication test failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())