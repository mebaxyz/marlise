#!/usr/bin/env python3
"""
Session Manager Startup Script

Runs the session manager service from the repository root with proper Python path.
"""
import sys
from pathlib import Path

# Add session_manager to Python path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Now import and run
from session_manager.main import SessionManagerService
import asyncio

if __name__ == "__main__":
    service = SessionManagerService()
    asyncio.run(service.run())
