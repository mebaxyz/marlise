"""Real bridge pedalboard demo.

Create a pedalboard using the actual modhost-bridge process, load plugins
selected automatically or via CLI, and print a summary.

Usage examples:
  python offline_pedalboard_demo.py                # use first 2 available plugins
  python offline_pedalboard_demo.py --plugins URI1 URI2 URI3
  python offline_pedalboard_demo.py --list-only    # just list plugins

Environment:
  MODHOST_BRIDGE_ENDPOINT (default tcp://127.0.0.1:6000)
Ensure the modhost-bridge service is running before launching.
"""

import asyncio
import logging
import sys

from core.plugin_manager import PluginManager
from core.session_manager import SessionManager
from core.bridge_client import BridgeClient

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("pedalboard_demo")



async def run_real_demo():

    bridge = BridgeClient()
    await bridge.start()
    plugin_manager = PluginManager(bridge)
    await plugin_manager.initialize()
    available = await plugin_manager.get_available_plugins()

    session_manager = SessionManager(plugin_manager, bridge, service_bus=None)
    create_res = await session_manager.create_pedalboard("offline_test")
    logger.info("Created pedalboard id=%s", create_res.get("pedalboard_id"))

    chosen_uris = ['http://lv2plug.in/plugins/eg-amp']
    '''chosen_uris = await choose_plugins(available, args.plugins, args.count)
    if not chosen_uris:
        logger.error("No suitable plugins selected to load.")
    else:
        logger.info("Loading %d plugin(s):", len(chosen_uris))'''
    loaded_instances = []
    for idx, uri in enumerate(chosen_uris):
        try:
            load_res = await plugin_manager.load_plugin(uri, x=idx * 180, y=100 + (idx % 2) * 120)
            loaded_instances.append(load_res["instance_id"])
            logger.info("  Loaded %s -> %s", uri, load_res["instance_id"])
        except Exception as e:
            logger.error("  Failed to load %s: %s", uri, e)

    # Setup system I/O routing if at least one plugin
    if loaded_instances:
        # Explicitly connect one system capture to the first plugin input and
        # the first plugin output to the first system playback so demo wires
        # a real signal path: capture -> effect -> playback
        pb = session_manager.pedalboard_service.current_pedalboard
        if not pb:
            logger.error("No current pedalboard found; skipping I/O wiring")
        else:
            system_inputs = pb.get_system_inputs()
            system_outputs = pb.get_system_outputs()
        first_instance = loaded_instances[0]

        # Connect capture_1 -> plugin:in_1
        try:
            if not system_inputs:
                raise RuntimeError("no system inputs discovered")
            src = system_inputs[0]
            tgt = f"{first_instance}:in_1"
            res = await bridge.call("modhost_bridge", "connect_jack_ports", port1=src, port2=tgt)
            if res.get("success"):
                logger.info("Connected %s -> %s", src, tgt)
            else:
                logger.error("Failed to connect %s -> %s: %s", src, tgt, res.get("error"))
        except Exception as e:
            logger.error("Exception while connecting input: %s", e)

        # Connect plugin:out_1 -> playback_1
        try:
            if not system_outputs:
                raise RuntimeError("no system outputs discovered")
            src = f"{first_instance}:out_1"
            tgt = system_outputs[0]
            res = await bridge.call("modhost_bridge", "connect_jack_ports", port1=src, port2=tgt)
            if res.get("success"):
                logger.info("Connected %s -> %s", src, tgt)
            else:
                logger.error("Failed to connect %s -> %s: %s", src, tgt, res.get("error"))
        except Exception as e:
            logger.error("Exception while connecting output: %s", e)

    # Optionally persist
    '''if not args.no_save:
        try:
            save_res = await session_manager.save_pedalboard()
            logger.info("Saved pedalboard to id=%s path=%s", save_res.get("saved_id"), save_res.get("saved_path"))
        except Exception as e:
            logger.error("Failed to save pedalboard: %s", e)
    else:
        logger.info("Skipping save (--no-save specified)")

    # Snapshot
    pb_state = await session_manager.get_current_pedalboard(persist=not args.no_save)
    pb_inner = pb_state.get("pedalboard") or {}
    logger.info(
        "Summary: name='%s' plugins=%d system_inputs=%s system_outputs=%s",
        pb_inner.get("name"),
        len(pb_inner.get("plugins", [])),
        pb_inner.get("system_inputs"),
        pb_inner.get("system_outputs"),
    )

    # Show a concise JSON excerpt (no datetime expansion)
    serialized = serialize_pedalboard(session_manager.pedalboard_service.current_pedalboard)
    minimal = {k: serialized[k] for k in ["id", "name", "plugins", "system_inputs", "system_outputs"] if k in serialized}
    logger.debug("Serialized excerpt: %s", minimal)
    '''
    await bridge.stop()
    logger.info("Demo complete.")
    return 0


def main():  # pragma: no cover - manual utility
    exit_code = asyncio.run(run_real_demo())
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
