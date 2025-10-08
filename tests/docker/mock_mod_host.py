#!/usr/bin/env python3
"""
Mock mod-host service for testing
Simulates the mod-host TCP interface for test purposes
"""

import asyncio
import json
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockModHost:
    def __init__(self, command_port=5555, feedback_port=5556):
        self.command_port = command_port
        self.feedback_port = feedback_port
        self.plugins = {}
        self.next_instance_id = 1
        self.server = None
        self.feedback_server = None
        
    async def handle_command(self, reader, writer):
        """Handle incoming mod-host commands"""
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                    
                command = data.decode().strip()
                logger.info(f"Received command: {command}")
                
                response = self.process_command(command)
                writer.write((response + "\n").encode())
                await writer.drain()
                
        except Exception as e:
            logger.error(f"Command handler error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def process_command(self, command):
        """Process mod-host protocol commands"""
        parts = command.split()
        if not parts:
            return "resp -1"
            
        cmd = parts[0]
        
        if cmd == "add":
            # add <lv2_uri> <instance_number>
            if len(parts) >= 2:
                uri = parts[1]
                instance_id = self.next_instance_id
                self.next_instance_id += 1
                
                self.plugins[instance_id] = {
                    "uri": uri,
                    "instance_id": instance_id,
                    "parameters": {
                        "gain": 0.5,
                        "bypass": False
                    }
                }
                logger.info(f"Loaded plugin {uri} as instance {instance_id}")
                return f"resp {instance_id}"
            return "resp -1"
            
        elif cmd == "remove":
            # remove <instance_number>
            if len(parts) >= 2:
                try:
                    instance_id = int(parts[1])
                    if instance_id in self.plugins:
                        del self.plugins[instance_id]
                        logger.info(f"Removed plugin instance {instance_id}")
                        return "resp 0"
                except ValueError:
                    pass
            return "resp -1"
            
        elif cmd == "param_set":
            # param_set <instance_number> <param_symbol> <param_value>
            if len(parts) >= 4:
                try:
                    instance_id = int(parts[1])
                    param_symbol = parts[2]
                    param_value = float(parts[3])
                    
                    if instance_id in self.plugins:
                        self.plugins[instance_id]["parameters"][param_symbol] = param_value
                        logger.info(f"Set parameter {param_symbol}={param_value} for instance {instance_id}")
                        return "resp 0"
                except ValueError:
                    pass
            return "resp -1"
            
        elif cmd == "param_get":
            # param_get <instance_number> <param_symbol>
            if len(parts) >= 3:
                try:
                    instance_id = int(parts[1])
                    param_symbol = parts[2]
                    
                    if instance_id in self.plugins:
                        value = self.plugins[instance_id]["parameters"].get(param_symbol, 0.0)
                        return f"resp {value}"
                except ValueError:
                    pass
            return "resp -1"
            
        elif cmd == "connect":
            # connect <output_port> <input_port>
            logger.info(f"Mock connection: {' '.join(parts[1:])}")
            return "resp 0"
            
        elif cmd == "disconnect":
            # disconnect <output_port> <input_port>  
            logger.info(f"Mock disconnection: {' '.join(parts[1:])}")
            return "resp 0"
            
        elif cmd == "cpu_load":
            # Return mock CPU load
            return "resp 15.2"
            
        elif cmd == "help":
            return "resp help add remove param_set param_get connect disconnect cpu_load"
            
        else:
            logger.warning(f"Unknown command: {cmd}")
            return "resp -1"
    
    async def start(self):
        """Start the mock mod-host servers"""
        # Command server
        self.server = await asyncio.start_server(
            self.handle_command, 
            '0.0.0.0', 
            self.command_port
        )
        
        # Feedback server (just for completeness)  
        self.feedback_server = await asyncio.start_server(
            lambda r, w: None,
            '0.0.0.0',
            self.feedback_port
        )
        
        logger.info(f"Mock mod-host started on ports {self.command_port} (command) and {self.feedback_port} (feedback)")
        
        async with self.server:
            await self.server.serve_forever()
    
    def stop(self):
        """Stop the servers"""
        if self.server:
            self.server.close()
        if self.feedback_server:
            self.feedback_server.close()

async def main():
    mock_host = MockModHost()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        mock_host.stop()
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await mock_host.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())