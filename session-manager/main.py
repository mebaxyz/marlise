"""
MOD UI - Session Manager Service

High-level session management service that coordinates pedalboard operations,
plugin management, and state persistence through the modhost-bridge service.
"""

# Localized pylint - module requires use of global variables for runtime wiring
# pylint: disable=global-statement

import asyncio
import logging
import os
import signal
from typing import Any, Dict

from zmq_service import ZMQService

# Local components
from core.plugin_manager import PluginManager
from core.session_manager import SessionManager
from handlers.zmq_handlers import ZMQHandlers
from core.bridge_client import ServiceBusCompatibleBridgeClient

# Configuration
SERVICE_NAME = "session_manager"

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components
# These module-level globals are intentionally used for simple runtime
# wiring between the startup/shutdown lifecycle and other modules. They are
# rebound during startup() and cleared in shutdown() so the module can be
# restarted during tests or by a supervisor.
plugin_manager = None
session_manager = None
zmq_service = None
bridge_client = None
# Running flag used by the main event loop to determine when to exit.
running = False


async def startup():
    """Start the session-manager service.

    This function performs the following high-level steps:
    - starts the ZeroMQ service used for RPC/pubsub
    - connects to the modhost-bridge via the bridge client (with retries)
    - initializes the plugin manager and session manager
    - registers ZeroMQ handlers

    Raises:
        Exception: when a critical component (bridge client, zmq) fails to
        start after the configured number of retries. Any exception will
        trigger a graceful shutdown attempt and be re-raised to the caller.
    """
    global zmq_service, plugin_manager, session_manager, bridge_client, running

    logger.info("Starting %s service", SERVICE_NAME)

    # If already started, don't start again
    try:
        if (
            zmq_service is not None
            and getattr(zmq_service, "is_running", lambda: False)()
        ):
            logger.info("Service already started")
            return

        # Initialize ZeroMQ service
        zmq_service = ZMQService(SERVICE_NAME)
        await zmq_service.start()
        logger.info("ZeroMQ service started")

        # Initialize bridge client for communication with modhost-bridge service
        bridge_client = ServiceBusCompatibleBridgeClient()

        # Attempt to start the bridge client with a small retry loop. This
        # helps when modhost-bridge is starting concurrently and may not be
        # immediately available. Configure via env vars:
        # BRIDGE_CONNECT_RETRIES (default 5)
        # BRIDGE_CONNECT_RETRY_DELAY (seconds, default 1.0)
        retries = int(os.environ.get("BRIDGE_CONNECT_RETRIES", "5"))
        delay = float(os.environ.get("BRIDGE_CONNECT_RETRY_DELAY", "1.0"))

        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                await bridge_client.start()
                logger.info("Bridge client started (attempt %s)", attempt)
                last_exc = None
                break
            except Exception as exc:  # pragma: no cover - runtime network issues
                last_exc = exc
                logger.warning(
                    "Bridge client start attempt %s/%s failed: %s",
                    attempt,
                    retries,
                    exc,
                )
                if attempt < retries:
                    await asyncio.sleep(delay)

        if last_exc:
            logger.error("Unable to start bridge client after %s attempts", retries)
            raise last_exc

        # Initialize plugin manager with bridge client
        plugin_manager = PluginManager(bridge_client, zmq_service)
        await plugin_manager.initialize()
        logger.info("Plugin manager initialized")

        # Initialize session manager
        session_manager = SessionManager(plugin_manager, bridge_client, zmq_service)
        logger.info("Session manager initialized")

        # Optionally auto-create a default pedalboard on startup.
        # Controlled via environment variable SESSION_MANAGER_AUTO_CREATE_DEFAULT.
        # This keeps behaviour opt-in and avoids surprising side-effects for
        # existing deployments.
        try:
            auto_create = os.environ.get("SESSION_MANAGER_AUTO_CREATE_DEFAULT", "0")
            if str(auto_create) in ("1", "true", "True", "yes", "on"):
                # Run create_pedalboard asynchronously and don't block startup for
                # long-running plugin loads; create a small task so startup returns
                # quickly while the creation proceeds.
                logger.info("Auto-create default pedalboard requested; creating...")
                asyncio.create_task(session_manager.create_pedalboard("Default"))
        except Exception:
            # Non-fatal: log and continue
            logger.exception("Failed to auto-create default pedalboard")

        # Register ZeroMQ methods
        handlers = ZMQHandlers(
            bridge_client, plugin_manager, session_manager, zmq_service
        )
        handlers.register_service_methods()

        # Mark the service as running and log successful startup.
        running = True
        logger.info("%s service started successfully", SERVICE_NAME)

    except Exception as e:
        # Log and attempt a best-effort shutdown so resources are cleaned up.
        logger.error("Failed to start %s service: %s", SERVICE_NAME, e)
        await shutdown()
        # Re-raise so the caller (or process supervisor) can observe failure.
        raise


async def shutdown():
    """Shut down the session-manager service gracefully.

    This will stop managed components in the reverse order of startup:
    - session manager (if running)
    - plugin manager
    - bridge client
    - ZeroMQ service

    The function is idempotent: calling it multiple times is safe and will
    simply attempt to stop components that still exist.
    """
    global zmq_service, plugin_manager, session_manager, bridge_client, running

    logger.info("Shutting down %s service", SERVICE_NAME)
    running = False

    if session_manager:
        logger.info("Shutting down session manager")

    if plugin_manager:
        await plugin_manager.shutdown()
        logger.info("Plugin manager shutdown")

    if bridge_client:
        await bridge_client.stop()
        logger.info("Bridge client stopped")

    if zmq_service:
        await zmq_service.stop()
        logger.info("ZeroMQ service stopped")

    # Clear globals so future startup attempts can rebind sockets and
    # resources. This also helps tests isolate state between runs.
    zmq_service = None
    bridge_client = None
    plugin_manager = None
    session_manager = None


async def main():
    """Main service entry point.

    This coroutine boots the service and installs signal handlers so the
    process can be stopped with SIGINT/SIGTERM. The main loop waits while the
    `running` flag is True and yields to the event loop periodically.
    """
    try:
        # Start the service
        await startup()

        # Setup signal handlers for graceful shutdown. Handlers schedule the
        # async shutdown() coroutine to run in the event loop.
        def signal_handler(signum, _frame):
            logger.info("Received signal %s, shutting down...", signum)
            asyncio.create_task(shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep the service running until shutdown() clears the `running` flag.
        while running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        # Allow Ctrl-C to stop the service in interactive runs.
        logger.info("Service interrupted by user")
    except Exception as e:
        # Log and propagate unexpected exceptions so they are visible to the
        # process supervisor.
        logger.error("Service failed: %s", e)
        raise
    finally:
        # Ensure shutdown is attempted before exiting.
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
