"""
System control and snapshot ZMQ handlers
"""
import logging
from datetime import datetime
from typing import Any, Dict

from .decorators import zmq_handler

logger = logging.getLogger(__name__)


class SystemHandlers:
    """System control and snapshot ZMQ RPC method handlers"""

    def __init__(self, bridge_client, plugin_manager, session_manager, zmq_service, config_manager=None):
        self.bridge_client = bridge_client
        self.plugin_manager = plugin_manager
        self.session_manager = session_manager
        self.zmq_service = zmq_service
        self.config_manager = config_manager

    def register_handlers(self):
        """Register all system control and snapshot handlers using decorator discovery"""
        # Handlers are registered via @zmq_handler decorator by the parent class
        pass

    # System control handlers
    @zmq_handler("get_system_status")
    async def handle_get_system_status(self, **_kwargs) -> Dict[str, Any]:
        """Get system status"""
        try:
            import psutil
            import os
            
            # Get basic system information
            status = {
                "uptime": os.popen("uptime").read().strip(),
                "load_avg": os.getloadavg(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "cpu_percent": psutil.cpu_percent(interval=1),
                "timestamp": datetime.now().isoformat()
            }
            
            return {"success": True, "status": status}
        except ImportError:
            # Fallback if psutil not available
            return {"success": True, "status": {"message": "Basic system monitoring - install psutil for detailed stats"}}
        except Exception as e:
            logger.error("Failed to get system status: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("shutdown")
    async def handle_shutdown(self, **_kwargs) -> Dict[str, Any]:
        """Shutdown system"""
        try:
            import subprocess
            
            # Execute system shutdown command
            result = subprocess.run(
                ["sudo", "shutdown", "-h", "now"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "System shutdown initiated"}
            else:
                return {"success": False, "error": f"Shutdown failed: {result.stderr}"}
        except subprocess.TimeoutExpired:
            return {"success": True, "message": "Shutdown command sent (timeout expected)"}
        except Exception as e:
            logger.error("Failed to shutdown: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("reboot")
    async def handle_reboot(self, **_kwargs) -> Dict[str, Any]:
        """Reboot system"""
        try:
            import subprocess
            
            # Execute system reboot command
            result = subprocess.run(
                ["sudo", "reboot"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {"success": True, "message": "System reboot initiated"}
            else:
                return {"success": False, "error": f"Reboot failed: {result.stderr}"}
        except subprocess.TimeoutExpired:
            return {"success": True, "message": "Reboot command sent (timeout expected)"}
        except Exception as e:
            logger.error("Failed to reboot: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_system_info")
    async def handle_get_system_info(self, **_kwargs) -> Dict[str, Any]:
        """Get system information"""
        try:
            import platform
            import os
            
            # Gather system information
            info = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version()
            }
            
            # Add additional info with fallbacks
            try:
                # Get uptime
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    info["uptime"] = uptime_seconds
            except Exception:
                info["uptime"] = None
                
            try:
                # Get memory info
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip()
                            if key in ["MemTotal", "MemFree", "MemAvailable"]:
                                meminfo[key] = value
                    info["memory"] = meminfo
            except Exception:
                info["memory"] = None
                
            # Add psutil info if available
            try:
                import psutil
                info["cpu_count"] = psutil.cpu_count()
                info["boot_time"] = psutil.boot_time()
            except ImportError:
                info["cpu_count"] = os.cpu_count()
                info["boot_time"] = None
                
            return {"success": True, "system_info": info}
        except Exception as e:
            logger.error("Failed to get system info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_cpu_usage")
    async def handle_get_cpu_usage(self, **_kwargs) -> Dict[str, Any]:
        """Get CPU usage"""
        try:
            import os
            
            # Try to get CPU usage from /proc/stat or fallback methods
            try:
                import psutil
                cpu_usage = {
                    "overall": psutil.cpu_percent(interval=1),
                    "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                    "load_avg": os.getloadavg()
                }
            except ImportError:
                # Fallback using load average
                load_avg = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                cpu_usage = {
                    "load_avg": load_avg,
                    "estimated_percent": min(load_avg[0] * 100 / cpu_count, 100)
                }
            
            return {"success": True, "cpu_usage": cpu_usage}
        except Exception as e:
            logger.error("Failed to get CPU usage: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_memory_usage")
    async def handle_get_memory_usage(self, **_kwargs) -> Dict[str, Any]:
        """Get memory usage"""
        try:
            try:
                import psutil
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                memory_usage = {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "swap_total": swap.total,
                    "swap_used": swap.used,
                    "swap_percent": swap.percent
                }
            except ImportError:
                # Fallback using /proc/meminfo
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            key, value = line.split(':')
                            meminfo[key] = int(value.strip().split()[0]) * 1024  # Convert kB to bytes
                    
                    total = meminfo.get('MemTotal', 0)
                    free = meminfo.get('MemFree', 0)
                    available = meminfo.get('MemAvailable', free)
                    used = total - available
                    
                    memory_usage = {
                        "total": total,
                        "available": available,
                        "used": used,
                        "percent": (used / total * 100) if total > 0 else 0
                    }
                except (FileNotFoundError, ValueError):
                    return {"success": False, "error": "Unable to read memory information"}
            
            return {"success": True, "memory_usage": memory_usage}
        except Exception as e:
            logger.error("Failed to get memory usage: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_disk_usage")
    async def handle_get_disk_usage(self, **_kwargs) -> Dict[str, Any]:
        """Get disk usage"""
        try:
            import shutil
            
            try:
                import psutil
                # Get all mounted disk partitions
                partitions = psutil.disk_partitions()
                disk_usage = {}
                
                for partition in partitions:
                    try:
                        partition_usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage[partition.mountpoint] = {
                            "device": partition.device,
                            "fstype": partition.fstype,
                            "total": partition_usage.total,
                            "used": partition_usage.used,
                            "free": partition_usage.free,
                            "percent": (partition_usage.used / partition_usage.total * 100) if partition_usage.total > 0 else 0
                        }
                    except PermissionError:
                        # Some mount points may not be accessible
                        continue
            except ImportError:
                # Fallback using shutil.disk_usage for root partition
                try:
                    total, used, free = shutil.disk_usage('/')
                    disk_usage = {
                        "/": {
                            "total": total,
                            "used": used,
                            "free": free,
                            "percent": (used / total * 100) if total > 0 else 0
                        }
                    }
                except OSError:
                    return {"success": False, "error": "Unable to get disk usage information"}
            
            return {"success": True, "disk_usage": disk_usage}
        except Exception as e:
            logger.error("Failed to get disk usage: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_network_info")
    async def handle_get_network_info(self, **_kwargs) -> Dict[str, Any]:
        """Get network information"""
        try:
            import socket
            import subprocess
            
            network_info = {}
            
            # Get hostname and basic info
            network_info["hostname"] = socket.gethostname()
            
            try:
                import psutil
                # Get network interfaces and their addresses
                interfaces = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                
                network_info["interfaces"] = {}
                for interface_name, addresses in interfaces.items():
                    interface_info = {
                        "addresses": [],
                        "is_up": stats[interface_name].isup if interface_name in stats else False
                    }
                    
                    for addr in addresses:
                        interface_info["addresses"].append({
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })
                    
                    network_info["interfaces"][interface_name] = interface_info
                    
            except ImportError:
                # Fallback using ip command or ifconfig
                try:
                    result = subprocess.run(['ip', 'addr', 'show'], 
                                          capture_output=True, text=True, timeout=5)
                    network_info["ip_addr_output"] = result.stdout
                except (subprocess.SubprocessError, FileNotFoundError):
                    try:
                        result = subprocess.run(['ifconfig'], 
                                              capture_output=True, text=True, timeout=5)
                        network_info["ifconfig_output"] = result.stdout
                    except (subprocess.SubprocessError, FileNotFoundError):
                        network_info["error"] = "Network tools not available"
            
            return {"success": True, "network_info": network_info}
        except Exception as e:
            logger.error("Failed to get network info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_logs")
    async def handle_get_logs(self, **kwargs) -> Dict[str, Any]:
        """Get system logs"""
        try:
            lines = kwargs.get("lines", 100)
            log_type = kwargs.get("type", "system")  # system, session, mod-host, etc.
            
            logs = {}
            
            if log_type == "system":
                # Try to get system logs via journalctl or syslog
                import subprocess
                try:
                    result = subprocess.run(['journalctl', '-n', str(lines), '--no-pager'], 
                                          capture_output=True, text=True, timeout=10)
                    logs["system"] = result.stdout.split('\n')[-lines:]
                except (subprocess.SubprocessError, FileNotFoundError):
                    try:
                        result = subprocess.run(['tail', '-n', str(lines), '/var/log/syslog'], 
                                              capture_output=True, text=True, timeout=10)
                        logs["system"] = result.stdout.split('\n')
                    except (subprocess.SubprocessError, FileNotFoundError):
                        logs["system"] = ["System logs not accessible"]
                        
            elif log_type == "session":
                # Get session manager logs
                log_files = [
                    "/home/nicolas/project/marlise/logs/session-manager.log",
                    "logs/session-manager.log"
                ]
                for log_file in log_files:
                    try:
                        with open(log_file, 'r') as f:
                            all_lines = f.readlines()
                            logs["session"] = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        break
                    except FileNotFoundError:
                        continue
                else:
                    logs["session"] = ["Session logs not found"]
                    
            elif log_type == "mod-host":
                # Get mod-host logs  
                log_files = [
                    "/home/nicolas/project/marlise/logs/mod-host.log",
                    "logs/mod-host.log"
                ]
                for log_file in log_files:
                    try:
                        with open(log_file, 'r') as f:
                            all_lines = f.readlines()
                            logs["mod-host"] = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        break
                    except FileNotFoundError:
                        continue
                else:
                    logs["mod-host"] = ["Mod-host logs not found"]
            else:
                return {"success": False, "error": f"Unknown log type: {log_type}"}
            
            return {"success": True, "logs": logs, "lines_requested": lines}
        except Exception as e:
            logger.error("Failed to get logs: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("clear_logs")
    async def handle_clear_logs(self, **kwargs) -> Dict[str, Any]:
        """Clear system logs"""
        try:
            log_type = kwargs.get("type", "session")  # Only clear app logs, not system logs
            
            cleared = []
            
            if log_type == "session":
                # Clear session manager logs
                log_files = [
                    "/home/nicolas/project/marlise/logs/session-manager.log",
                    "logs/session-manager.log"
                ]
                for log_file in log_files:
                    try:
                        with open(log_file, 'w') as f:
                            f.write("")  # Truncate file
                        cleared.append(log_file)
                    except (FileNotFoundError, PermissionError):
                        continue
                        
            elif log_type == "mod-host":
                # Clear mod-host logs
                log_files = [
                    "/home/nicolas/project/marlise/logs/mod-host.log", 
                    "logs/mod-host.log"
                ]
                for log_file in log_files:
                    try:
                        with open(log_file, 'w') as f:
                            f.write("")  # Truncate file
                        cleared.append(log_file)
                    except (FileNotFoundError, PermissionError):
                        continue
                        
            elif log_type == "all":
                # Clear all application logs (but not system logs)
                log_files = [
                    "/home/nicolas/project/marlise/logs/session-manager.log",
                    "/home/nicolas/project/marlise/logs/mod-host.log",
                    "/home/nicolas/project/marlise/logs/modhost-bridge.log",
                    "logs/session-manager.log",
                    "logs/mod-host.log", 
                    "logs/modhost-bridge.log"
                ]
                for log_file in log_files:
                    try:
                        with open(log_file, 'w') as f:
                            f.write("")  # Truncate file
                        cleared.append(log_file)
                    except (FileNotFoundError, PermissionError):
                        continue
            else:
                return {"success": False, "error": f"Invalid log type: {log_type}. Use 'session', 'mod-host', or 'all'"}
            
            if cleared:
                return {"success": True, "message": "Cleared logs", "cleared_files": cleared}
            else:
                return {"success": False, "error": "No log files found or accessible"}
                
        except Exception as e:
            logger.error("Failed to clear logs: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_config")
    async def handle_get_config(self, **kwargs) -> Dict[str, Any]:
        """Get system configuration"""
        try:
            key = kwargs.get("key")
            if not key:
                return {"success": False, "error": "Missing 'key' parameter"}
            # Use config_manager if available
            if self.config_manager:
                val = await self.config_manager.get_setting(key)
                return {"success": True, "key": key, "value": val}
            else:
                return {"success": False, "error": "Config manager not available"}
        except Exception as e:
            logger.error("Failed to get config: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("reset_config")
    async def handle_reset_config(self, **_kwargs) -> Dict[str, Any]:
        """Reset system configuration"""
        try:
            if self.config_manager:
                ok = await self.config_manager.reset_config()
                return {"success": ok}
            else:
                return {"success": False, "error": "Config manager not available"}
        except Exception as e:
            logger.error("Failed to reset config: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_config")
    async def handle_set_config(self, **kwargs) -> Dict[str, Any]:
        """Set a configuration key to a value"""
        try:
            key = kwargs.get("key")
            value = kwargs.get("value")
            if not key:
                return {"success": False, "error": "Missing 'key' parameter"}

            if self.config_manager:
                ok = await self.config_manager.set_config(key, value)
                return {"success": ok}

            return {"success": False, "error": "Config manager not available"}
        except Exception as e:
            logger.error("Failed to set config: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("ping_hmi")
    async def handle_ping_hmi(self, **_kwargs) -> Dict[str, Any]:
        """Ping HMI (Hardware Machine Interface) for connection status and latency"""
        try:
            # This would need to be implemented via HMI communication
            return {"success": False, "error": "Ping HMI not implemented"}
        except Exception as e:
            logger.error("Failed to ping HMI: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("reset_session")
    async def handle_reset_session(self, **_kwargs) -> Dict[str, Any]:
        """Reset current session to empty pedalboard state"""
        try:
            # Use session manager to reset the session
            await self.session_manager.reset_session()
            return {"success": True, "message": "Session reset to empty state"}
        except Exception as e:
            logger.error("Failed to reset session: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_truebypass")
    async def handle_set_truebypass(self, **kwargs) -> Dict[str, Any]:
        """Control hardware true bypass relays"""
        try:
            channel = kwargs.get("channel")
            state = kwargs.get("state")

            if not channel or state is None:
                return {"success": False, "error": "Missing 'channel' or 'state' parameter"}

            # Forward to bridge client for hardware relay control
            result = await self.bridge_client.call("set_truebypass", channel=channel, state=state)
            return result
        except Exception as e:
            logger.error("Failed to set truebypass: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("set_buffer_size")
    async def handle_set_buffer_size(self, **kwargs) -> Dict[str, Any]:
        """Change JACK audio buffer size"""
        try:
            size = kwargs.get("size")

            if size is None or size not in [128, 256]:
                return {"success": False, "error": "Invalid buffer size"}

            # Forward to bridge for JACK control
            result = await self.bridge_client.call("set_buffer_size", size=size)
            return result
        except Exception as e:
            logger.error("Failed to set buffer size: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("reset_xruns")
    async def handle_reset_xruns(self, **_kwargs) -> Dict[str, Any]:
        """Reset JACK audio dropout (xrun) counter"""
        try:
            # Forward to bridge for JACK monitoring
            result = await self.bridge_client.call("reset_xruns")
            return result
        except Exception as e:
            logger.error("Failed to reset xruns: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("switch_cpu_frequency")
    async def handle_switch_cpu_frequency(self, **_kwargs) -> Dict[str, Any]:
        """Toggle CPU frequency scaling between performance and powersave modes"""
        try:
            import subprocess
            import glob
            
            # Get current governor for CPU 0
            try:
                with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                    current_governor = f.read().strip()
            except FileNotFoundError:
                return {"success": False, "error": "CPU frequency scaling not supported on this system"}
            
            # Toggle between performance and powersave
            new_governor = "performance" if current_governor == "powersave" else "powersave"
            
            # Get all CPU cores
            cpu_paths = glob.glob('/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor')
            
            if not cpu_paths:
                return {"success": False, "error": "No CPU frequency scaling files found"}
            
            # Apply new governor to all cores
            try:
                for cpu_path in cpu_paths:
                    subprocess.run(
                        ["sudo", "tee", cpu_path],
                        input=new_governor,
                        text=True,
                        check=True,
                        capture_output=True
                    )
                
                return {
                    "success": True, 
                    "message": f"CPU governor switched from {current_governor} to {new_governor}",
                    "previous_governor": current_governor,
                    "new_governor": new_governor
                }
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Failed to set CPU governor: {e.stderr}"}
                
        except Exception as e:
            logger.error("Failed to switch CPU frequency: %s", e)
            return {"success": False, "error": str(e)}

    # Snapshot handlers
    @zmq_handler("save_snapshot")
    async def handle_save_snapshot(self, **kwargs) -> Dict[str, Any]:
        """Save current plugin parameter states as a snapshot"""
        try:
            name = kwargs.get("name", f"Snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            result = await self.session_manager.create_snapshot(name)
            return {"success": True, "snapshot": result["snapshot"]}
        except Exception as e:
            logger.error("Failed to save snapshot: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("save_snapshot_as")
    async def handle_save_snapshot_as(self, **kwargs) -> Dict[str, Any]:
        """Save current state as a new named snapshot"""
        try:
            title = kwargs.get("title")
            if not title:
                return {"success": False, "error": "Missing 'title' parameter"}

            result = await self.session_manager.create_snapshot(title)
            return {"success": True, "snapshot": result["snapshot"]}
        except Exception as e:
            logger.error("Failed to save snapshot as: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("rename_snapshot")
    async def handle_rename_snapshot(self, **kwargs) -> Dict[str, Any]:
        """Change the name of an existing snapshot"""
        try:
            snapshot_id = kwargs.get("id")
            title = kwargs.get("title")

            if snapshot_id is None or not title:
                return {"success": False, "error": "Missing 'id' or 'title' parameter"}

            # Use session manager to rename snapshot
            result = await self.session_manager.rename_snapshot(snapshot_id, title)
            return result
        except Exception as e:
            logger.error("Failed to rename snapshot: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_snapshot")
    async def handle_remove_snapshot(self, **kwargs) -> Dict[str, Any]:
        """Delete a snapshot"""
        try:
            snapshot_id = kwargs.get("id")
            if snapshot_id is None:
                return {"success": False, "error": "Missing 'id' parameter"}

            # Use session manager to remove snapshot
            result = await self.session_manager.remove_snapshot(snapshot_id)
            return result
        except Exception as e:
            logger.error("Failed to remove snapshot: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("list_snapshots")
    async def handle_list_snapshots(self, **_kwargs) -> Dict[str, Any]:
        """Get all snapshots for current pedalboard"""
        try:
            result = await self.session_manager.list_snapshots()
            return {"success": True, "snapshots": result.get("snapshots", [])}
        except Exception as e:
            logger.error("Failed to list snapshots: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_snapshot_name")
    async def handle_get_snapshot_name(self, **kwargs) -> Dict[str, Any]:
        """Get the name of a specific snapshot"""
        try:
            snapshot_id = kwargs.get("id")
            if snapshot_id is None:
                return {"success": False, "error": "Missing 'id' parameter"}

            # Use session manager to get snapshot info
            result = await self.session_manager.get_snapshot_info(snapshot_id)
            if result.get("success"):
                return {"success": True, "name": result["snapshot"]["name"]}
            else:
                return result
        except Exception as e:
            logger.error("Failed to get snapshot name: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("load_snapshot")
    async def handle_load_snapshot(self, **kwargs) -> Dict[str, Any]:
        """Load a snapshot, restoring all parameter values"""
        try:
            snapshot_id = kwargs.get("id")
            if snapshot_id is None:
                return {"success": False, "error": "Missing 'id' parameter"}

            result = await self.session_manager.apply_snapshot(snapshot_id)
            return result
        except Exception as e:
            logger.error("Failed to load snapshot: %s", e)
            return {"success": False, "error": str(e)}



    # Bank and preset handlers
    @zmq_handler("get_banks")
    async def handle_get_banks(self, **_kwargs) -> Dict[str, Any]:
        """Get banks"""
        try:
            # Use session manager to get banks (collections of pedalboards)
            result = await self.session_manager.get_banks()
            return result
        except Exception as e:
            logger.error("Failed to get banks: %s", e)
            return {"success": False, "error": str(e)}

    # Favorites management handlers
    @zmq_handler("add_favorite")
    async def handle_add_favorite(self, **kwargs) -> Dict[str, Any]:
        """Add a plugin to user's favorites list"""
        try:
            uri = kwargs.get("uri")
            if not uri:
                return {"success": False, "error": "Missing 'uri' parameter"}

            # Use session manager to add favorite plugin
            result = await self.session_manager.add_favorite_plugin(uri)
            return result
        except Exception as e:
            logger.error("Failed to add favorite: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_favorite")
    async def handle_remove_favorite(self, **kwargs) -> Dict[str, Any]:
        """Remove a plugin from user's favorites list"""
        try:
            uri = kwargs.get("uri")
            if not uri:
                return {"success": False, "error": "Missing 'uri' parameter"}

            # Use session manager to remove favorite plugin
            result = await self.session_manager.remove_favorite_plugin(uri)
            return result
        except Exception as e:
            logger.error("Failed to remove favorite: %s", e)
            return {"success": False, "error": str(e)}

    # Recording management handlers
    @zmq_handler("start_recording")
    async def handle_start_recording(self, **kwargs) -> Dict[str, Any]:
        """Start recording audio from the current pedalboard"""
        try:
            filename = kwargs.get("filename")
            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}

            # Use session manager to start recording
            result = await self.session_manager.start_recording(filename)
            return result
        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("stop_recording")
    async def handle_stop_recording(self, **_kwargs) -> Dict[str, Any]:
        """Stop audio recording and finalize the file"""
        try:
            # Use session manager to stop recording
            result = await self.session_manager.stop_recording()
            return result
        except Exception as e:
            logger.error("Failed to stop recording: %s", e)
            return {"success": False, "error": str(e)}

    # File operation handlers
    @zmq_handler("list_files")
    async def handle_list_files(self, **kwargs) -> Dict[str, Any]:
        """List files"""
        try:
            import os
            
            path = kwargs.get("path", "/home/nicolas/project/marlise/data")  # Default to data directory
            file_type = kwargs.get("type", "all")  # audio, pedalboard, all
            
            if not os.path.exists(path):
                return {"success": False, "error": f"Path does not exist: {path}"}
                
            if not os.path.isdir(path):
                return {"success": False, "error": f"Path is not a directory: {path}"}
            
            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    file_info = {
                        "name": item,
                        "path": item_path,
                        "is_directory": os.path.isdir(item_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    }
                    
                    if file_type == "audio" and not item.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.aiff')):
                        continue
                    elif file_type == "pedalboard" and not item.lower().endswith('.json'):
                        continue
                        
                    files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
                    
            return {"success": True, "files": files, "path": path}
        except Exception as e:
            logger.error("Failed to list files: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("upload_file")
    async def handle_upload_file(self, **kwargs) -> Dict[str, Any]:
        """Upload file"""
        try:
            import os
            import base64
            
            filename = kwargs.get("filename")
            data = kwargs.get("data")
            target_dir = kwargs.get("target_dir", "/home/nicolas/project/marlise/data/uploads")

            if not filename or data is None:
                return {"success": False, "error": "Missing 'filename' or 'data' parameter"}

            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Build full file path
            file_path = os.path.join(target_dir, filename)
            
            # Prevent directory traversal attacks
            if not file_path.startswith(target_dir):
                return {"success": False, "error": "Invalid filename - directory traversal not allowed"}
            
            # Decode base64 data if needed
            try:
                if isinstance(data, str):
                    # Assume base64 encoded
                    file_data = base64.b64decode(data)
                else:
                    file_data = data
            except Exception:
                return {"success": False, "error": "Invalid file data format"}
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            file_size = os.path.getsize(file_path)
            
            return {"success": True, "filename": filename, "path": file_path, "size": file_size}
        except Exception as e:
            logger.error("Failed to upload file: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("download_file")
    async def handle_download_file(self, **kwargs) -> Dict[str, Any]:
        """Download file"""
        try:
            import os
            import base64
            
            filename = kwargs.get("filename") 
            base_dir = kwargs.get("base_dir", "/home/nicolas/project/marlise/data")
            
            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}

            # Build full file path
            file_path = os.path.join(base_dir, filename)
            
            # Security check - ensure file is within base directory
            if not file_path.startswith(base_dir):
                return {"success": False, "error": "Invalid filename - directory traversal not allowed"}
            
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {filename}"}
                
            if not os.path.isfile(file_path):
                return {"success": False, "error": f"Path is not a file: {filename}"}
            
            # Read and encode file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Encode as base64 for transmission
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            file_size = len(file_data)
            
            return {
                "success": True, 
                "filename": filename, 
                "data": encoded_data,
                "size": file_size,
                "encoding": "base64"
            }
        except Exception as e:
            logger.error("Failed to download file: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("delete_file")
    async def handle_delete_file(self, **kwargs) -> Dict[str, Any]:
        """Delete file"""
        try:
            import os
            
            filename = kwargs.get("filename")
            base_dir = kwargs.get("base_dir", "/home/nicolas/project/marlise/data")
            
            if not filename:
                return {"success": False, "error": "Missing 'filename' parameter"}

            # Build full file path
            file_path = os.path.join(base_dir, filename)
            
            # Security check - ensure file is within base directory  
            if not file_path.startswith(base_dir):
                return {"success": False, "error": "Invalid filename - directory traversal not allowed"}
            
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {filename}"}
                
            if not os.path.isfile(file_path):
                return {"success": False, "error": f"Path is not a file: {filename}"}
            
            # Delete the file
            os.remove(file_path)
            
            return {"success": True, "message": f"File deleted: {filename}"}
        except Exception as e:
            logger.error("Failed to delete file: %s", e)
            return {"success": False, "error": str(e)}

    # Update and package handlers
    @zmq_handler("check_updates")
    async def handle_check_updates(self, **_kwargs) -> Dict[str, Any]:
        """Check for updates"""
        try:
            import subprocess
            
            # Check for git updates
            try:
                # Get current branch and check for updates
                result = subprocess.run(['git', 'fetch', '--dry-run'], 
                                      capture_output=True, text=True, timeout=10)
                
                status_result = subprocess.run(['git', 'status', '-uno'], 
                                             capture_output=True, text=True, timeout=5)
                
                updates_available = "Your branch is behind" in status_result.stdout or len(result.stderr) > 0
                
                return {
                    "success": True, 
                    "updates_available": updates_available,
                    "git_status": status_result.stdout,
                    "fetch_result": result.stderr
                }
            except (subprocess.SubprocessError, FileNotFoundError):
                # Git not available or not in git repo
                return {
                    "success": True,
                    "updates_available": False,
                    "message": "Git not available or not in a git repository"
                }
        except Exception as e:
            logger.error("Failed to check updates: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("install_update")
    async def handle_install_update(self, **kwargs) -> Dict[str, Any]:
        """Install update"""
        try:
            import subprocess
            
            version = kwargs.get("version", "latest")
            
            try:
                # For git-based updates
                if version == "latest":
                    # Pull latest changes from current branch
                    result = subprocess.run(['git', 'pull'], 
                                          capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        return {
                            "success": True, 
                            "message": "Updated to latest version",
                            "git_output": result.stdout
                        }
                    else:
                        return {
                            "success": False, 
                            "error": f"Git pull failed: {result.stderr}"
                        }
                else:
                    # Checkout specific version/tag
                    result = subprocess.run(['git', 'checkout', version], 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Updated to version {version}",
                            "git_output": result.stdout
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Git checkout failed: {result.stderr}"
                        }
            except (subprocess.SubprocessError, FileNotFoundError):
                return {"success": False, "error": "Git not available or update failed"}
        except Exception as e:
            logger.error("Failed to install update: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_packages")
    async def handle_get_packages(self, **_kwargs) -> Dict[str, Any]:
        """Get packages"""
        try:
            import subprocess
            
            packages = {}
            
            # Get Python packages
            try:
                result = subprocess.run(['pip', 'list', '--format=json'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    import json
                    pip_packages = json.loads(result.stdout)
                    packages["python"] = pip_packages
            except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
                packages["python"] = []
            
            # Get system packages (apt/dpkg)
            try:
                result = subprocess.run(['dpkg', '-l'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Parse dpkg output (simplified)
                    lines = result.stdout.split('\n')[5:]  # Skip header
                    system_packages = []
                    for line in lines:
                        if line.strip() and line.startswith('ii'):
                            parts = line.split()
                            if len(parts) >= 3:
                                system_packages.append({
                                    "name": parts[1],
                                    "version": parts[2],
                                    "status": "installed"
                                })
                    packages["system"] = system_packages[:100]  # Limit output
            except (subprocess.SubprocessError, FileNotFoundError):
                packages["system"] = []
            
            return {"success": True, "packages": packages}
        except Exception as e:
            logger.error("Failed to get packages: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("install_package")
    async def handle_install_package(self, **kwargs) -> Dict[str, Any]:
        """Install package"""
        try:
            import subprocess
            
            package_name = kwargs.get("package_name")
            package_type = kwargs.get("type", "python")  # python, system
            
            if not package_name:
                return {"success": False, "error": "Missing 'package_name' parameter"}

            if package_type == "python":
                # Install Python package via pip
                try:
                    result = subprocess.run(['pip', 'install', package_name], 
                                          capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Python package '{package_name}' installed successfully",
                            "output": result.stdout
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to install package: {result.stderr}"
                        }
                except (subprocess.SubprocessError, FileNotFoundError):
                    return {"success": False, "error": "pip not available"}
                    
            elif package_type == "system":
                # System packages require root privileges - not implemented for security
                return {
                    "success": False, 
                    "error": "System package installation requires root privileges - not supported"
                }
            else:
                return {"success": False, "error": f"Unknown package type: {package_type}"}
        except Exception as e:
            logger.error("Failed to install package: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("remove_package")
    async def handle_remove_package(self, **kwargs) -> Dict[str, Any]:
        """Remove package"""
        try:
            import subprocess
            
            package_name = kwargs.get("package_name")
            package_type = kwargs.get("type", "python")  # python, system
            
            if not package_name:
                return {"success": False, "error": "Missing 'package_name' parameter"}

            if package_type == "python":
                # Remove Python package via pip
                try:
                    result = subprocess.run(['pip', 'uninstall', package_name, '-y'], 
                                          capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Python package '{package_name}' removed successfully",
                            "output": result.stdout
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to remove package: {result.stderr}"
                        }
                except (subprocess.SubprocessError, FileNotFoundError):
                    return {"success": False, "error": "pip not available"}
                    
            elif package_type == "system":
                # System packages require root privileges - not implemented for security
                return {
                    "success": False,
                    "error": "System package removal requires root privileges - not supported"
                }
            else:
                return {"success": False, "error": f"Unknown package type: {package_type}"}
        except Exception as e:
            logger.error("Failed to remove package: %s", e)
            return {"success": False, "error": str(e)}

    # Authentication handlers
    @zmq_handler("login")
    async def handle_login(self, **kwargs) -> Dict[str, Any]:
        """Login"""
        try:
            username = kwargs.get("username")
            password = kwargs.get("password")

            if not username or not password:
                return {"success": False, "error": "Missing 'username' or 'password' parameter"}

            # Use session manager for authentication
            result = await self.session_manager.authenticate_user(username, password)
            return result
        except Exception as e:
            logger.error("Failed to login: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("logout")
    async def handle_logout(self, **kwargs) -> Dict[str, Any]:
        """Logout"""
        try:
            session_token = kwargs.get("session_token")
            
            # Use session manager to logout
            result = await self.session_manager.logout_user(session_token)
            return result
        except Exception as e:
            logger.error("Failed to logout: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("get_user_info")
    async def handle_get_user_info(self, **kwargs) -> Dict[str, Any]:
        """Get user information"""
        try:
            session_token = kwargs.get("session_token")
            
            # Use session manager to get user info
            result = await self.session_manager.get_user_info(session_token)
            return result
        except Exception as e:
            logger.error("Failed to get user info: %s", e)
            return {"success": False, "error": str(e)}

    @zmq_handler("address_parameter")
    async def handle_address_parameter(self, **kwargs) -> Dict[str, Any]:
        """Address a plugin parameter to hardware control or MIDI CC"""
        try:
            instance_id = kwargs.get("instance_id")
            symbol = kwargs.get("symbol")
            uri = kwargs.get("uri")
            label = kwargs.get("label")
            minimum = kwargs.get("minimum")
            maximum = kwargs.get("maximum")
            value = kwargs.get("value")
            steps = kwargs.get("steps", 33)
            tempo = kwargs.get("tempo", False)
            dividers = kwargs.get("dividers")
            page = kwargs.get("page", 0)
            subpage = kwargs.get("subpage", 0)
            coloured = kwargs.get("coloured", False)
            momentary = kwargs.get("momentary", False)
            operational_mode = kwargs.get("operational_mode", "=")

            if not instance_id or not symbol:
                return {"success": False, "error": "Missing 'instance_id' or 'symbol' parameter"}

            if not uri or not label or minimum is None or maximum is None or value is None:
                return {"success": False, "error": "Missing required addressing parameters"}

            # Forward to bridge client for parameter addressing
            result = await self.bridge_client.call("address_parameter", 
                instance_id=instance_id,
                symbol=symbol,
                uri=uri,
                label=label,
                minimum=minimum,
                maximum=maximum,
                value=value,
                steps=steps,
                tempo=tempo,
                dividers=dividers,
                page=page,
                subpage=subpage,
                coloured=coloured,
                momentary=momentary,
                operational_mode=operational_mode
            )
            return result
        except Exception as e:
            logger.error("Failed to address parameter: %s", e)
            return {"success": False, "error": str(e)}

