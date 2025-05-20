#!/usr/bin/env python3
import json
from typing import Dict, Any

def collect_arguments_interactively(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect arguments interactively based on the tool's schema.
    Args:
        schema: The input schema for the tool.
    Returns:
        Dictionary of collected arguments.
    """
    if not schema:
        print("No schema available for this tool.")
        return {}
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    collected_args = {}
    
    print("\nCollecting arguments for the tool:")
    print("=" * 40)
    
    # First collect required arguments
    for prop_name in required:
        if prop_name in properties:
            prop_info = properties[prop_name]
            prop_type = prop_info.get("type", "string")
            description = prop_info.get("description", "No description available")
            
            print(f"\n[REQUIRED] {prop_name} ({prop_type})")
            print(f"Description: {description}")
            
            while True:
                user_input = input(f"Enter value for {prop_name}: ").strip()
                if user_input:
                    try:
                        # Try to parse the input based on the expected type
                        if prop_type == "integer":
                            collected_args[prop_name] = int(user_input)
                        elif prop_type == "number":
                            collected_args[prop_name] = float(user_input)
                        elif prop_type == "boolean":
                            collected_args[prop_name] = user_input.lower() in ("true", "1", "yes", "y")
                        elif prop_type == "array":
                            # Try to parse as JSON array
                            collected_args[prop_name] = json.loads(user_input)
                        elif prop_type == "object":
                            # Try to parse as JSON object
                            collected_args[prop_name] = json.loads(user_input)
                        else:
                            # Default to string
                            collected_args[prop_name] = user_input
                        break
                    except (ValueError, json.JSONDecodeError) as e:
                        print(f"Error parsing input: {e}")
                        print(f"Expected type: {prop_type}")
                        if prop_type in ["array", "object"]:
                            print("Please provide valid JSON format.")
                        continue
                else:
                    print("This field is required. Please provide a value.")
    
    # Then collect optional arguments
    optional_props = [prop for prop in properties if prop not in required]
    if optional_props:
        print("\n" + "=" * 40)
        print("Optional arguments (press Enter to skip):")
        
        for prop_name in optional_props:
            prop_info = properties[prop_name]
            prop_type = prop_info.get("type", "string")
            description = prop_info.get("description", "No description available")
            default = prop_info.get("default")
            
            print(f"\n[OPTIONAL] {prop_name} ({prop_type})")
            print(f"Description: {description}")
            if default is not None:
                print(f"Default: {default}")
            
            user_input = input(f"Enter value for {prop_name} (or press Enter to skip): ").strip()
            if user_input:
                try:
                    # Try to parse the input based on the expected type
                    if prop_type == "integer":
                        collected_args[prop_name] = int(user_input)
                    elif prop_type == "number":
                        collected_args[prop_name] = float(user_input)
                    elif prop_type == "boolean":
                        collected_args[prop_name] = user_input.lower() in ("true", "1", "yes", "y")
                    elif prop_type == "array":
                        # Try to parse as JSON array
                        collected_args[prop_name] = json.loads(user_input)
                    elif prop_type == "object":
                        # Try to parse as JSON object
                        collected_args[prop_name] = json.loads(user_input)
                    else:
                        # Default to string
                        collected_args[prop_name] = user_input
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Error parsing input: {e}. Skipping this argument.")
                    continue
    
    return collected_args