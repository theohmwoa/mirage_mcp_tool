#!/usr/bin/env python3
import os
import json
import asyncio
from typing import Dict, List, Optional, Any

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcptools.core import list_tools, get_tool_schema, call_tool
from mcptools.utils import collect_arguments_interactively

class MCPCliApp:
    def __init__(self, config_file: str = "mcp_config.json"):
        self.config_file = config_file
        self.managed_mcp_servers = {}  # Stores {name: {"command": "cmd", "args": [...]}}
        self.load_config()
    
    def load_config(self):
        """Load MCP server configurations from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.managed_mcp_servers = json.load(f)
                print(f"Loaded {len(self.managed_mcp_servers)} MCP server configurations.")
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.managed_mcp_servers = {}
    
    def save_config(self):
        """Save MCP server configurations to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.managed_mcp_servers, f, indent=2)
            print(f"Saved {len(self.managed_mcp_servers)} MCP server configurations.")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def add_mcp_server(self, name: str, command: str, args: List[str], env_vars: Optional[Dict[str, str]] = None):
        """Add a new MCP server configuration."""
        if name in self.managed_mcp_servers:
            print(f"Warning: Overwriting existing MCP server configuration '{name}'.")
        
        self.managed_mcp_servers[name] = {
            "command": command,
            "args": args,
            "env": env_vars if env_vars else {}
        }
        env_str = f" with env: {env_vars}" if env_vars else ""
        print(f"Added MCP server '{name}': {command} {' '.join(args)}{env_str}")
        self.save_config()
    
    def remove_mcp_server(self, name: str):
        """Remove an MCP server configuration."""
        if name not in self.managed_mcp_servers:
            print(f"Error: MCP server '{name}' not found in configurations.")
            return False
        
        del self.managed_mcp_servers[name]
        print(f"Removed MCP server '{name}'.")
        self.save_config()
        return True
    
    def list_mcp_servers(self):
        """List all configured MCP servers."""
        if not self.managed_mcp_servers:
            print("No MCP servers configured. Use 'add' command to add one.")
            return
        
        print("\nConfigured MCP servers:")
        for name, config in self.managed_mcp_servers.items():
            command = config["command"]
            args = config["args"]
            env = config.get("env", {})
            env_str = f" with env: {env}" if env else ""
            print(f"  {name}: {command} {' '.join(args)}{env_str}")
    
    async def list_mcp_actions(self, mcp_name: str):
        """List all actions available on the specified MCP server."""
        if mcp_name not in self.managed_mcp_servers:
            print(f"ERROR: MCP server '{mcp_name}' not found in configurations.")
            return
        
        config = self.managed_mcp_servers[mcp_name]
        command = config["command"]
        args_list = config["args"]
        env_config = config.get("env")
        
        # Log configuration details
        print(f"DEBUG: MCP server '{mcp_name}' configuration:")
        print(f"DEBUG: Command: {command}")
        print(f"DEBUG: Arguments: {args_list}")
        print(f"DEBUG: Environment variables: {list(env_config.keys()) if env_config else 'None'}")
        
        server_params = StdioServerParameters(command=command, args=args_list, env=env_config or None)
        print(f"\nAttempting to connect to '{mcp_name}' ({command} {' '.join(args_list)}) to list actions...")
        try:
            print(f"DEBUG: Creating stdio client for '{mcp_name}'")
            async with stdio_client(server_params) as (read_stream, write_stream):
                try:
                    print(f"DEBUG: Establishing session with '{mcp_name}'")
                    async with ClientSession(read_stream, write_stream) as session:
                        try:
                            print(f"DEBUG: Initializing session with '{mcp_name}'")
                            await session.initialize()
                            print(f"DEBUG: Successfully initialized session with '{mcp_name}'")
                            print(f"Successfully connected to '{mcp_name}'. Fetching actions...")
                            try:
                                await list_tools(session)  # Use the provided list_tools function
                            except asyncio.CancelledError as ce:
                                print(f"ERROR: Session was cancelled during tool listing: {ce}")
                                print(f"DEBUG: This could be due to a timeout or connection issue with '{mcp_name}'")
                                import traceback
                                traceback.print_exc()
                            except Exception as e:
                                print(f"ERROR: Failed to list tools for '{mcp_name}': {str(e)}")
                                import traceback
                                traceback.print_exc()
                        except asyncio.CancelledError as ce:
                            print(f"ERROR: Session was cancelled during initialization: {ce}")
                            print(f"DEBUG: This could be due to a timeout or connection issue with '{mcp_name}'")
                            import traceback
                            traceback.print_exc()
                        except Exception as e:
                            print(f"ERROR: Failed to initialize session with '{mcp_name}': {str(e)}")
                            import traceback
                            traceback.print_exc()
                except Exception as e:
                    print(f"ERROR: Failed to establish session with '{mcp_name}': {str(e)}")
                    import traceback
                    traceback.print_exc()
        except FileNotFoundError:
            print(f"ERROR: The command '{command}' was not found. Please ensure it's in your PATH or provide the full path.")
        except ConnectionRefusedError:
            print(f"ERROR: Connection refused by the MCP server. Is '{command} {' '.join(args_list)}' running correctly and is it an MCP server?")
        except asyncio.TimeoutError:
            print(f"ERROR: Timeout while trying to connect or communicate with '{mcp_name}'.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while listing actions for '{mcp_name}': {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"DEBUG: Connection to '{mcp_name}' closed.")
            print(f"Disconnected from '{mcp_name}'.")
    
    async def execute_mcp_action(self, mcp_name: str, action_name: str, action_args: Optional[Dict[str, Any]] = None, interactive: bool = False):
        """Execute an action on the specified MCP server."""
        if mcp_name not in self.managed_mcp_servers:
            print(f"Error: MCP server '{mcp_name}' not found in configurations.")
            return
        
        config = self.managed_mcp_servers[mcp_name]
        command = config["command"]
        args_list = config["args"]
        env_config = config.get("env")
        
        server_params = StdioServerParameters(command=command, args=args_list, env=env_config or None)
        print(f"\nAttempting to connect to '{mcp_name}' to execute action '{action_name}'...")
        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    print(f"Successfully connected to '{mcp_name}'.")
                    
                    if interactive or action_args is None:
                        print(f"\nFetching schema for action '{action_name}'...")
                        schema = await get_tool_schema(session, action_name)
                        print(f"Schema for action '{action_name}':")
                        print(json.dumps(schema, indent=2))
                        if schema:
                            print(f"\nTool schema for '{action_name}':")
                            print(json.dumps(schema, indent=2))
                            action_args = collect_arguments_interactively(schema)
                        else:
                            print(f"Warning: Could not retrieve schema for action '{action_name}'.")
                            action_args = action_args or {}
                    
                    print(f"Executing action with arguments: {action_args}")
                    await call_tool(session, action_name, action_args)
        except FileNotFoundError:
            print(f"Error: The command '{command}' was not found. Please ensure it's in your PATH or provide the full path.")
        except ConnectionRefusedError:
            print(f"Error: Connection refused by the MCP server. Is '{command} {' '.join(args_list)}' running correctly and is it an MCP server?")
        except asyncio.TimeoutError:
            print(f"Error: Timeout while trying to connect or communicate with '{mcp_name}'.")
        except Exception as e:
            print(f"An unexpected error occurred while executing action '{action_name}' on '{mcp_name}': {e}")
            # import traceback
            # traceback.print_exc()
        finally:
            print(f"Disconnected from '{mcp_name}'.")