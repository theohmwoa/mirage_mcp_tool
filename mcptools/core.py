#!/usr/bin/env python3
import json
import asyncio
import traceback
from typing import Dict, List, Any, Optional

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def list_tools(session: ClientSession):
    """List all tools available on the MCP server."""
    try:
        print("DEBUG: Requesting tool list from MCP server...")
        tools_response = await session.list_tools()
        tools = tools_response.tools
        print(f"DEBUG: Received response with {len(tools)} tools")
        
        if not tools:
            print("No tools available on this MCP server.")
            return
        
        print("\nAvailable tools:")
        for tool in tools:
            name = tool.name or "Unknown"
            description = tool.description or "No description available"
            print(f"  {name}: {description}")
            
    except asyncio.CancelledError as ce:
        print(f"ERROR: Session was cancelled during tool listing: {ce}")
        print("DEBUG: This could be due to a timeout or connection issue with the MCP server")
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"\nERROR: Failed to list tools: {str(e)}")
        print("DEBUG: Full exception details:")
        traceback.print_exc()

async def get_tool_schema(session: ClientSession, tool_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema for a specific tool."""
    try:
        print(f"DEBUG: Requesting tool list to find schema for '{tool_name}'")
        tools_response = await session.list_tools()
        tools = tools_response.tools
        print(f"DEBUG: Received response with {len(tools)} tools")
        
        for tool in tools:
            if tool.name == tool_name:
                print(f"DEBUG: Found schema for tool '{tool_name}'")
                return tool.parameters
        
        print(f"WARNING: No schema found for tool '{tool_name}'")
        return None
    except asyncio.CancelledError as ce:
        print(f"ERROR: Session was cancelled while getting schema for '{tool_name}': {ce}")
        print("DEBUG: This could be due to a timeout or connection issue with the MCP server")
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"ERROR: Failed to get schema for tool '{tool_name}': {str(e)}")
        print("DEBUG: Full exception details:")
        traceback.print_exc()
        raise

async def call_tool(session: ClientSession, tool_name: str, args: Dict[str, Any] = None):
    """Call a tool on the MCP server."""
    if args is None:
        args = {}
    
    try:
        print(f"DEBUG: Calling tool '{tool_name}' with arguments: {json.dumps(args, indent=2)}")
        result = await session.call_tool(tool_name, args)
        
        if result.isError:
            print(f"ERROR: Tool execution failed: {result}")
            print(f"DEBUG: Error details for '{tool_name}': {json.dumps(result.error, indent=2) if hasattr(result, 'error') else 'No detailed error information'}")
        else:
            print(f"DEBUG: Tool '{tool_name}' executed successfully")
            print(f"DEBUG: Result: {result}")
        
        return result
    except asyncio.CancelledError as ce:
        print(f"ERROR: Session was cancelled during execution of tool '{tool_name}': {ce}")
        print(f"DEBUG: This could be due to a timeout or connection issue with the MCP server")
        print(f"DEBUG: Arguments passed to tool: {json.dumps(args, indent=2)}")
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"ERROR: Failed to execute tool '{tool_name}': {e}")
        print(f"DEBUG: Arguments passed to tool: {json.dumps(args, indent=2)}")
        print(f"DEBUG: Full exception details:")
        traceback.print_exc()
        raise

# New functions for the API

import traceback
from typing import List, Dict, Any

async def get_tools_with_schemas(server_name: str, app) -> List[Dict[str, Any]]:
    """
    Get all tools with their schemas from an MCP server.
    
    Args:
        server_name: Name of the MCP server configuration
        app: MCPCliApp instance
        
    Returns:
        List of tool information including name, description, and schema
    """
    try:
        if server_name not in app.managed_mcp_servers:
            print(f"ERROR: MCP server '{server_name}' not found in configuration")
            raise ValueError(f"MCP server '{server_name}' not found")

        config = app.managed_mcp_servers[server_name]
        command = config["command"]
        args_list = config["args"]
        env_config = config.get("env")
        
        print(f"DEBUG: Preparing to connect to {server_name} MCP server at {command}")
        print(f"DEBUG: Using arguments: {args_list}")
        print(f"DEBUG: Environment variables configured: {list(env_config.keys()) if env_config else 'None'}")

        server_params = StdioServerParameters(command=command, args=args_list, env=env_config or None)

        tools_with_schemas = []

        try:
            print(f"DEBUG: Establishing connection to {server_name} MCP server")
            async with stdio_client(server_params) as (read_stream, write_stream):
                try:
                    print(f"DEBUG: Creating client session for {server_name} MCP server")
                    async with ClientSession(read_stream, write_stream) as session:
                        try:
                            print(f"DEBUG: Initializing session with {server_name} MCP server")
                            await session.initialize()
                            print(f"DEBUG: Session initialized successfully, requesting tool list")
                            tools_response = await session.list_tools()
                            tools = tools_response.tools
                            print(f"DEBUG: Received {len(tools)} tools from {server_name} MCP server")
                        except asyncio.CancelledError as ce:
                            print(f"ERROR: Session was cancelled during initialization or tool listing: {ce}")
                            print(f"DEBUG: This could indicate a timeout or connection issue with {server_name} MCP server")
                            traceback.print_exc()
                            return []
                        except Exception as session_error:
                            print(f"ERROR: Failed during session operations with {server_name} MCP server: {session_error}")
                            print("DEBUG: Full exception details:")
                            traceback.print_exc()
                            return []

                        for tool in tools:
                            try:
                                tools_with_schemas.append({
                                    "name": tool.name or "Unknown",
                                    "description": tool.description or "No description available",
                                    "schema": tool.inputSchema or {}
                                })
                                print(f"DEBUG: Successfully retrieved schema for tool '{tool.name}, schema: {tool.inputSchema}'")
                            except Exception as tool_error:
                                print(f"ERROR: Failed to process tool information: {tool_error}")
                                print(f"DEBUG: Tool data: {tool}")
                                print("DEBUG: Full exception details:")
                                traceback.print_exc()
                except Exception as session_error:
                    print(f"ERROR: Failed to create session with {server_name} MCP server: {session_error}")
                    print("DEBUG: Full exception details:")
                    traceback.print_exc()
                    return []
        except FileNotFoundError:
            print(f"ERROR: The command '{command}' was not found. Please ensure it's in your PATH or provide the full path.")
            return []
        except ConnectionRefusedError:
            print(f"ERROR: Connection refused by the {server_name} MCP server. Is '{command} {' '.join(args_list)}' running correctly and is it an MCP server?")
            return []
        except asyncio.TimeoutError:
            print(f"ERROR: Timeout while trying to connect to {server_name} MCP server.")
            return []
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while connecting to {server_name} MCP server: {e}")
            print("DEBUG: Full exception details:")
            traceback.print_exc()
            return []

        print(f"DEBUG: Successfully retrieved {len(tools_with_schemas)} tools with schemas from {server_name} MCP server")
        return tools_with_schemas

    except Exception as e:
        print(f"ERROR: An error occurred in get_tools_with_schemas: {e}")
        print("DEBUG: Full exception details:")
        traceback.print_exc()
        return []


async def execute_tool_and_get_result(server_name: str, tool_name: str, args: Dict[str, Any], app) -> Any:
    """
    Execute a tool on an MCP server and return the result.
    
    Args:
        server_name: Name of the MCP server configuration
        tool_name: Name of the tool to execute
        args: Arguments for the tool
        app: MCPCliApp instance
        
    Returns:
        Result of the tool execution
    """
    if server_name not in app.managed_mcp_servers:
        raise ValueError(f"MCP server '{server_name}' not found")
    
    config = app.managed_mcp_servers[server_name]
    command = config["command"]
    args_list = config["args"]
    env_config = config.get("env")
    
    server_params = StdioServerParameters(command=command, args=args_list, env=env_config or None)
    
    try:
        print(f"DEBUG: Connecting to {server_name} MCP server at {command}")
        async with stdio_client(server_params) as (read_stream, write_stream):
            try:
                print(f"DEBUG: Initializing session with {server_name} MCP server")
                async with ClientSession(read_stream, write_stream) as session:
                    try:
                        await session.initialize()
                        print(f"DEBUG: Successfully initialized session with {server_name} MCP server")
                        print(f"DEBUG: Calling tool '{tool_name}' with args: {json.dumps(args, indent=2)}")
                        result = await session.call_tool(tool_name, args)
                        print(f"DEBUG: Tool execution completed. Result type: {type(result).__name__}")
                        return result
                    except asyncio.CancelledError as ce:
                        print(f"ERROR: Session was cancelled during tool execution: {ce}")
                        print(f"DEBUG: Context information - server: {server_name}, tool: {tool_name}")
                        raise
                    except Exception as e:
                        print(f"ERROR: Failed to execute tool '{tool_name}' on server '{server_name}': {e}")
                        print(f"DEBUG: Full exception details:")
                        traceback.print_exc()
                        raise
            except Exception as e:
                print(f"ERROR: Failed to initialize session with {server_name} MCP server: {e}")
                print(f"DEBUG: Full exception details:")
                traceback.print_exc()
                raise
    except FileNotFoundError:
        print(f"ERROR: The command '{command}' was not found. Please ensure it's in your PATH or provide the full path.")
        raise
    except ConnectionRefusedError:
        print(f"ERROR: Connection refused by the MCP server. Is '{command} {' '.join(args_list)}' running correctly and is it an MCP server?")
        raise
    except asyncio.TimeoutError:
        print(f"ERROR: Timeout while trying to connect or communicate with '{server_name}'.")
        raise
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while connecting to '{server_name}': {e}")
        print(f"DEBUG: Full exception details:")
        traceback.print_exc()
        raise