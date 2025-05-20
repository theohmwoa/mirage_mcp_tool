#!/usr/bin/env python3
import asyncio
import json
import argparse
from typing import Dict, Any

from mcptools.app import MCPCliApp

def parse_args():
    """
    Parse command-line arguments for the MCP CLI.
    Returns:
        Parsed arguments object.
    """
    parser = argparse.ArgumentParser(description="MCP CLI - Manage and interact with MCP servers")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add MCP server
    add_parser = subparsers.add_parser("add", help="Add a new MCP server configuration")
    add_parser.add_argument("name", help="Name for the MCP server configuration")
    add_parser.add_argument("command", help="Command to run the MCP server")
    add_parser.add_argument("args", nargs="*", help="Arguments for the MCP server command")
    add_parser.add_argument("--env", help="JSON string of environment variables for the server (e.g., '{\"KEY\": \"VALUE\"}')", default="{}")
    
    # Remove MCP server
    remove_parser = subparsers.add_parser("remove", help="Remove an MCP server configuration")
    remove_parser.add_argument("name", help="Name of the MCP server configuration to remove")
    
    # List MCP servers
    subparsers.add_parser("list", help="List all configured MCP servers")
    
    # List actions for an MCP server
    actions_parser = subparsers.add_parser("actions", help="List all actions available on an MCP server")
    actions_parser.add_argument("name", help="Name of the MCP server to list actions for")
    
    # Execute an action on an MCP server
    execute_parser = subparsers.add_parser("execute", help="Execute an action on an MCP server")
    execute_parser.add_argument("name", help="Name of the MCP server to execute the action on")
    execute_parser.add_argument("action", help="Name of the action to execute")
    execute_parser.add_argument("--args", help="JSON string of arguments for the action", default=None)
    execute_parser.add_argument("--interactive", "-i", action="store_true", help="Collect arguments interactively")
    
    return parser.parse_args()

async def interactive_menu(app: MCPCliApp):
    """
    Run the MCP CLI in interactive menu mode.
    Args:
        app: MCPCliApp instance for managing server configurations.
    """
    while True:
        print("\n===== MCP CLI Interactive Menu =====")
        print("1. List configured MCP servers")
        print("2. Add a new MCP server")
        print("3. Remove an MCP server")
        print("4. List actions for an MCP server")
        print("5. Execute an action on an MCP server")
        print("6. Execute an action with interactive argument collection")
        print("h. Help")
        print("0. Exit")
        
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice == "0":
            print("Exiting MCP CLI. Goodbye!")
            break
        elif choice == "1":
            app.list_mcp_servers()
        elif choice == "2":
            name = input("Enter a name for the MCP server: ")
            command = input("Enter the command to run the MCP server: ")
            args_str = input("Enter arguments for the command (space-separated): ")
            args = args_str.split() if args_str.strip() else []
            env_str = input("Enter environment variables as a JSON string (e.g., {\"KEY\": \"VALUE\"}) (default: {}): ") or "{}"
            try:
                env_vars = json.loads(env_str)
                app.add_mcp_server(name, command, args, env_vars)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON for environment variables: {env_str}")
        elif choice == "3":
            name = input("Enter the name of the MCP server to remove: ")
            app.remove_mcp_server(name)
        elif choice == "4":
            name = input("Enter the name of the MCP server to list actions for: ")
            await app.list_mcp_actions(name)
        elif choice == "5":
            name = input("Enter the name of the MCP server: ")
            action = input("Enter the name of the action to execute: ")
            args_str = input("Enter JSON arguments for the action (default: {}): ") or '{"q": "theohmwoa"}'
            try:
                action_args = json.loads(args_str)
                await app.execute_mcp_action(name, action, action_args)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in action arguments: {args_str}")
                print("Please provide a valid JSON string, e.g., '{\"param1\": \"value1\", \"param2\": 123}'")
        elif choice == "6":
            name = input("Enter the name of the MCP server: ")
            action = input("Enter the name of the action to execute: ")
            await app.execute_mcp_action(name, action, interactive=True)
        elif choice == "h":
            print("\nMCP CLI Help:")
            print("  1: List all configured MCP servers")
            print("  2: Add a new MCP server configuration")
            print("  3: Remove an existing MCP server configuration")
            print("  4: Connect to an MCP server and list available actions/tools")
            print("  5: Connect to an MCP server and execute a specific action/tool with JSON args")
            print("  6: Connect to an MCP server and execute an action with interactive argument collection")
            print("  0: Exit the application")
            print("\nThe MCP CLI allows you to manage and interact with MCP servers.")
            print("Each server connection is established when needed and closed after the operation.")
            print("\nInteractive argument collection helps you provide arguments step-by-step")
            print("based on the tool's schema, with type validation and descriptions.")
        else:
            print("Invalid choice. Please try again.")

async def main():
    """
    Main entry point for the MCP CLI application.
    Handles command-line arguments and interactive mode.
    """
    parser = argparse.ArgumentParser(description="MCP CLI - Manage and interact with MCP servers")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive menu mode")
    
    # Only parse known args first to check for interactive mode
    args, remaining = parser.parse_known_args()
    
    app = MCPCliApp()
    
    if args.interactive:
        await interactive_menu(app)
        return
    
    # If not in interactive mode, parse the command arguments
    args = parse_args()
    
    if not args.command:
        # If no command is provided, enter interactive mode
        print("No command specified. Entering interactive mode...")
        await interactive_menu(app)
        return
    
    if args.command == "add":
        try:
            env_vars = json.loads(args.env)
            app.add_mcp_server(args.name, args.command, args.args, env_vars)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in --env argument: {args.env}")
            print("Please provide a valid JSON string, e.g., '{\"KEY\": \"VALUE\"}'")
    elif args.command == "remove":
        app.remove_mcp_server(args.name)
    elif args.command == "list":
        app.list_mcp_servers()
    elif args.command == "actions":
        await app.list_mcp_actions(args.name)
    elif args.command == "execute":
        action_args = None
        if args.args:
            try:
                action_args = json.loads(args.args)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in action arguments: {args.args}")
                print("Please provide a valid JSON string, e.g., '{\"param1\": \"value1\", \"param2\": 123}'")
                return
        await app.execute_mcp_action(args.name, args.action, action_args, args.interactive)
    else:
        print("Unknown command. Use --help for available commands.")
        print("Or run with --interactive for menu mode.")