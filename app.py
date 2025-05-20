#!/usr/bin/env python3
import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from mcptools.app import MCPCliApp


# Initialize the FastAPI app
app = FastAPI(
    title="MCP CLI API",
    description="API for interacting with MCP (Machine Conversation Protocol) servers",
    version="1.0.0"
)

# Initialize the MCPCliApp
mcp_app = MCPCliApp()

# Define Pydantic models for request/response
class ServerConfig(BaseModel):
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}

class ServerResponse(BaseModel):
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]

class ServerListResponse(BaseModel):
    servers: List[ServerResponse]

class ActionResponse(BaseModel):
    name: str
    description: str
    schema: Dict[str, Any]

class ActionsListResponse(BaseModel):
    actions: List[ActionResponse]
    schemas: Dict[str, Dict[str, Any]]

class ExecuteActionRequest(BaseModel):
    args: Dict[str, Any] = {}

class ExecuteActionResponse(BaseModel):
    result: Any

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "MCP CLI API",
        "description": "API for interacting with MCP (Machine Conversation Protocol) servers",
        "endpoints": [
            "/servers",
            "/servers/{name}",
            "/servers/{name}/actions",
            "/servers/{name}/actions/{action_name}",
        ]
    }

@app.get("/servers", response_model=ServerListResponse, tags=["Servers"])
async def list_servers():
    """List all configured MCP servers."""
    servers = []
    for name, config in mcp_app.managed_mcp_servers.items():
        servers.append(ServerResponse(
            name=name,
            command=config["command"],
            args=config["args"],
            env=config.get("env", {})
        ))
    return ServerListResponse(servers=servers)

@app.post("/servers", response_model=ServerResponse, tags=["Servers"])
async def add_server(server: ServerConfig):
    """Add a new MCP server configuration."""
    mcp_app.add_mcp_server(server.name, server.command, server.args, server.env)
    return ServerResponse(
        name=server.name,
        command=server.command,
        args=server.args,
        env=server.env
    )

@app.delete("/servers/{name}", tags=["Servers"])
async def remove_server(name: str):
    """Remove an MCP server configuration."""
    if name not in mcp_app.managed_mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    
    success = mcp_app.remove_mcp_server(name)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to remove MCP server '{name}'")
    
    return {"message": f"Removed MCP server '{name}'"}

@app.get("/servers/{name}/actions", response_model=ActionsListResponse, tags=["Actions"])
async def list_actions(name: str, include_schemas: bool = Query(True, description="Include action schemas in response")):
    """
    List all actions available on the specified MCP server.
    
    If include_schemas is True, the response will include the full JSON schema for each action,
    which can be used for argument collection.
    """
    if name not in mcp_app.managed_mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    
    from mcptools.core import get_tools_with_schemas
    
    try:
        actions_with_schemas = await get_tools_with_schemas(name, mcp_app)
        
        # Format the response
        actions = []
        schemas = {}
        
        for action_info in actions_with_schemas:
            print(action_info["schema"])
            action_name = action_info["name"]
            action_description = action_info["description"]
            action_schema = action_info["schema"]

            actions.append(ActionResponse(
                name=action_name,
                description=action_description,
                schema=action_schema
            ))

            if include_schemas:
                schemas[action_name] = action_schema if action_schema else {}
        
        return ActionsListResponse(actions=actions, schemas=schemas)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing actions: {str(e)}")

@app.post("/servers/{name}/actions/{action_name}", response_model=ExecuteActionResponse, tags=["Actions"])
async def execute_action(name: str, action_name: str, request: ExecuteActionRequest):
    """Execute an action on the specified MCP server."""
    if name not in mcp_app.managed_mcp_servers:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")
    
    try:
        # We need to modify the core functionality to capture the result
        from mcptools.core import execute_tool_and_get_result
        
        result = await execute_tool_and_get_result(name, action_name, request.args, mcp_app)
        return ExecuteActionResponse(result=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing action: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)