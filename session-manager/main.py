"""
MOD UI - Session Manager Service

High-level session management service that coordinates pedalboard operations,
plugin management, and state persistence through the modhost-bridge service.
"""


import logging
import asyncio
from service import SessionManagerService

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    service = SessionManagerService()
    asyncio.run(service.run())
