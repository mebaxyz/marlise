"""
MOD UI - Session Manager Service

High-level session management service that coordinates pedalboard operations,
plugin management, and state persistence through the modhost-bridge service.
"""


"""
Session Manager Service

Encapsulates the high-level session manager lifecycle, state, and
orchestration for MOD UI pedalboard operations. Provides startup,
shutdown and main-loop management for the session manager service.

This module wires ZeroMQ and the bridge client into the higher-level
plugin/session managers used by the application.
"""

# Standard library imports
import asyncio
import logging
import os
import signal

# Third-party imports
import zmq

# Local imports
from .infrastructure.bridge_client import BridgeClient
from .managers.plugin_manager import PluginManager
from .managers.session_manager import SessionManager
from .handlers.zmq_handlers import ZMQHandlers
from .services.zmq_service import ZMQService

SERVICE_NAME = "session_manager"
logger = logging.getLogger(__name__)

class SessionManagerService:
    """
    Encapsulates all session manager service state and lifecycle.
    """
    def __init__(self):
        """Initialize an empty SessionManagerService instance.

        All managed components are set to None so startup() can bind
        and initialize resources when requested.
        """
        self.plugin_manager = None
        self.session_manager = None
        self.zmq_service = None
        self.bridge_client = None
        self.running = False

    async def startup(self):
        """Start and initialize all managed components.

        This will create and start the ZeroMQ service, connect the bridge
        client (with retries), initialize the plugin manager and session
        manager, register ZeroMQ handlers, and mark the service as running.

        Raises:
            Exception: if a critical component fails to start.
        """
        logger.info("Starting %s service", SERVICE_NAME)
        try:
            if (
                self.zmq_service is not None
                and getattr(self.zmq_service, "is_running", lambda: False)()
            ):
                logger.info("Service already started")
                return

            # Initialize ZeroMQ service
            self.zmq_service = ZMQService(SERVICE_NAME)
            await self.zmq_service.start()
            logger.info("ZeroMQ service started")

            # Initialize bridge client for communication with modhost-bridge service
            self.bridge_client = BridgeClient()

            # Attempt to start the bridge client with a small retry loop.
            retries = int(os.environ.get("BRIDGE_CONNECT_RETRIES", "5"))
            delay = float(os.environ.get("BRIDGE_CONNECT_RETRY_DELAY", "1.0"))

            for attempt in range(1, retries + 1):
                try:
                    await self.bridge_client.start()
                    logger.info("Bridge client started (attempt %s)", attempt)
                    last_exc = None
                    break
                except zmq.ZMQError as exc:
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
            self.plugin_manager = PluginManager(self.bridge_client, self.zmq_service)
            await self.plugin_manager.initialize()
            logger.info("Plugin manager initialized")

            # Initialize session manager
            self.session_manager = SessionManager(
                self.plugin_manager,
                self.bridge_client,
                self.zmq_service,
            )
            logger.info("Session manager initialized")

            # Optionally auto-create a default pedalboard on startup.
            auto_create = os.environ.get("SESSION_MANAGER_AUTO_CREATE_DEFAULT", "0")
            if str(auto_create) in ("1", "true", "True", "yes", "on"):
                logger.info("Auto-create default pedalboard requested; creating...")
                asyncio.create_task(self.session_manager.create_pedalboard("Default"))

            # Register ZeroMQ methods
            handlers = ZMQHandlers(
                self.bridge_client,
                self.plugin_manager,
                self.session_manager,
                self.zmq_service,
            )
            handlers.register_service_methods()

            # Mark the service as running and log successful startup.
            self.running = True
            logger.info("%s service started successfully", SERVICE_NAME)

        except Exception as e:
            logger.error("Failed to start %s service: %s", SERVICE_NAME, e)
            await self.shutdown()
            raise

    async def shutdown(self):
        """Shut down components and release resources.

        Stops managed components in the reverse order of startup and clears
        internal state so the service can be restarted later.
        """
        logger.info("Shutting down %s service", SERVICE_NAME)
        self.running = False

        if self.session_manager:
            logger.info("Shutting down session manager")

        if self.plugin_manager:
            await self.plugin_manager.shutdown()
            logger.info("Plugin manager shutdown")

        if self.bridge_client:
            await self.bridge_client.stop()
            logger.info("Bridge client stopped")

        if self.zmq_service:
            await self.zmq_service.stop()
            logger.info("ZeroMQ service stopped")

        # Clear state for future startup attempts
        self.zmq_service = None
        self.bridge_client = None
        self.plugin_manager = None
        self.session_manager = None

    async def run(self):
        """
        Main service entry point. Boots the service, installs signal handlers,
        and runs the main loop until shutdown is requested.
        """
        try:
            await self.startup()

            def signal_handler(signum, _frame):
                logger.info("Received signal %s, shutting down...", signum)
                asyncio.create_task(self.shutdown())

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Service interrupted by user")
        except Exception as e:
            logger.error("Service failed: %s", e)
            raise
        finally:
            await self.shutdown()


logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    service = SessionManagerService()
    asyncio.run(service.run())
