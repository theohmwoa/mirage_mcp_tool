# MCP CLI

A modular command-line interface for interacting with MCP (Machine Conversation Protocol) servers.

## Project Structure

The MCP CLI has been organized into a modular structure for better maintainability:

```
mcp/
  __init__.py     # Package initialization
  core.py         # Core MCP server interaction functions
  app.py          # MCPCliApp class for managing server configurations
  utils.py        # Utility functions like interactive argument collection
  cli.py          # Command-line interface and argument parsing
mcp_cli_new.py    # Main entry point script
```

## Usage

You can run the MCP CLI in two modes:

### Command-line Mode

```bash
# List all configured MCP servers
python mcp_cli_new.py list

# Add a new MCP server configuration
python mcp_cli_new.py add <name> <command> [args...] [--env '{"KEY": "VALUE"}']

# Remove an MCP server configuration
python mcp_cli_new.py remove <name>

# List actions available on an MCP server
python mcp_cli_new.py actions <name>

# Execute an action on an MCP server
python mcp_cli_new.py execute <name> <action> [--args '{"param": "value"}'] [--interactive]
```

### Interactive Mode

```bash
python mcp_cli_new.py --interactive
# or
python mcp_cli_new.py -i
```

In interactive mode, you'll be presented with a menu to choose operations and will be prompted for required information.

## Configuration

MCP server configurations are stored in `mcp_config.json` in the following format:

```json
{
  "server_name": {
    "command": "executable",
    "args": ["arg1", "arg2"],
    "env": {"ENV_VAR": "value"}
  }
}
```

## Migration from Old Version

To migrate from the old single-file version to the new modular version:

1. Ensure your `mcp_config.json` file is in the same directory as the new script
2. Start using `mcp_cli_new.py` instead of `mcp_cli.py`
3. All your existing configurations will be automatically loaded

## Dependencies

This tool requires the `mcp` Python package and its dependencies to be installed.