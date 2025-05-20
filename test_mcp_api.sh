#!/bin/bash

# Test script for MCP API Server
# This script tests all the endpoints of the MCP API Server

# Set the base URL for the API
API_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${YELLOW}==== $1 ====${NC}"
}

# Function to check if the API server is running
check_server() {
    print_header "Checking if API server is running"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}API server is running${NC}"
    else
        echo -e "${RED}API server is not running. Please start it with 'python3 app.py'${NC}"
        exit 1
    fi
}

# Function to test adding a new MCP server
test_add_server() {
    print_header "Testing: Add a new MCP server"
    
    # Create a test server configuration
    server_name="Github"
    
    echo "Adding server: $server_name"
    
    response=$(curl -s -X POST "$API_URL/servers" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$server_name\",
            \"command\": \"/Users/theophilushomawoo/Documents/MCP/githubmcp\",
            \"args\": [\"stdio\"],
            \"env\": {\"GITHUB_PERSONAL_ACCESS_TOKEN\": \"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\"}
        }")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool
    
    # Extract the name from the response to verify
    name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', ''))")
    
    if [ "$name" = "$server_name" ]; then
        echo -e "${GREEN}Successfully added server: $server_name${NC}"
        echo "$server_name" > /tmp/mcp_test_server
    else
        echo -e "${RED}Failed to add server${NC}"
        exit 1
    fi
}

# Function to test listing all MCP servers
test_list_servers() {
    print_header "Testing: List all MCP servers"
    
    response=$(curl -s "$API_URL/servers")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool
    
    # Check if the response contains servers
    servers_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('servers', [])))")
    
    if [ "$servers_count" -gt 0 ]; then
        echo -e "${GREEN}Successfully listed servers. Found $servers_count server(s)${NC}"
    else
        echo -e "${RED}No servers found or failed to list servers${NC}"
        exit 1
    fi
}

# Function to test listing actions for an MCP server
test_list_actions() {
    print_header "Testing: List actions for an MCP server"
    
    # Get the test server name
    server_name=$(cat /tmp/mcp_test_server)
    
    echo "Listing actions for server: $server_name"
    
    response=$(curl -s "$API_URL/servers/$server_name/actions")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool
    
    # Check if the response contains actions
    actions_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('actions', [])))")
    
    if [ "$actions_count" -gt 0 ]; then
        echo -e "${GREEN}Successfully listed actions. Found $actions_count action(s)${NC}"
        
        # Extract the first action name for later use
        action_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('actions', [])[0].get('name', ''))")
        echo "$action_name" > /tmp/mcp_test_action
    else
        echo -e "${RED}No actions found or failed to list actions${NC}"
        exit 1
    fi
}

# Function to test executing an action on an MCP server
test_execute_action() {
    print_header "Testing: Execute an action on an MCP server"
    
    # Get the test server name and action name
    server_name=$(cat /tmp/mcp_test_server)
    action_name=$(cat /tmp/mcp_test_action)
    
    echo "Executing action '$action_name' on server: $server_name"
    
    response=$(curl -s -X POST "$API_URL/servers/$server_name/actions/$action_name" \
        -H "Content-Type: application/json" \
        -d "{
            \"args\": {
                \"message\": \"Hello from test script!\"
            }
        }")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool
    
    # Check if the response contains a result
    has_result=$(echo "$response" | python3 -c "import sys, json; print('result' in json.load(sys.stdin))")
    
    if [ "$has_result" = "True" ]; then
        echo -e "${GREEN}Successfully executed action${NC}"
    else
        echo -e "${RED}Failed to execute action${NC}"
        exit 1
    fi
}

# Function to test removing an MCP server
test_remove_server() {
    print_header "Testing: Remove an MCP server"
    
    # Get the test server name
    server_name=$(cat /tmp/mcp_test_server)
    
    echo "Removing server: $server_name"
    
    response=$(curl -s -X DELETE "$API_URL/servers/$server_name")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool
    
    # Check if the response contains a success message
    message=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', ''))")
    
    if [[ "$message" == *"Removed MCP server"* ]]; then
        echo -e "${GREEN}Successfully removed server: $server_name${NC}"
        rm /tmp/mcp_test_server
        rm /tmp/mcp_test_action
    else
        echo -e "${RED}Failed to remove server${NC}"
        exit 1
    fi
    
    # Verify the server was removed by listing servers again
    response=$(curl -s "$API_URL/servers")
    servers=$(echo "$response" | python3 -c "import sys, json; print([s.get('name') for s in json.load(sys.stdin).get('servers', [])])")
    
    if [[ "$servers" == *"$server_name"* ]]; then
        echo -e "${RED}Server was not actually removed${NC}"
        exit 1
    else
        echo -e "${GREEN}Verified server was removed${NC}"
    fi
}

# Run all tests
check_server
test_add_server
test_list_servers
test_list_actions
test_execute_action


print_header "All tests completed successfully!"