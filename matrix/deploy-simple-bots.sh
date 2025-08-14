#!/bin/bash

# Deploy Simple Matrix Buddy Bots
# This script deploys the simple orchestrator and LLM bots

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOMELAB_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🤖 Deploying Simple Matrix Buddy Bots${NC}"
echo "======================================"

# Check if we're in the right directory
if [[ ! -f "$SCRIPT_DIR/simple-bots-compose.yml" ]]; then
    echo -e "${RED}❌ Error: simple-bots-compose.yml not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Check environment file
ENV_FILE="$HOMELAB_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}❌ Error: .env file not found at $ENV_FILE${NC}"
    exit 1
fi

# Source environment variables
source "$ENV_FILE"

# Passwords are hardcoded in docker-compose file for simplicity
echo -e "${GREEN}✅ Using existing bot credentials from setup${NC}"

# Function to check if container is running
check_container() {
    local container_name="$1"
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for container to be healthy
wait_for_healthy() {
    local container_name="$1"
    local max_attempts=30
    local attempt=0

    echo -n "Waiting for $container_name to be healthy..."

    while [[ $attempt -lt $max_attempts ]]; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | grep -q "healthy"; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    echo -e " ${RED}❌ Timeout${NC}"
    return 1
}

# Stop existing containers if running
echo -e "${YELLOW}🛑 Stopping existing simple bot containers...${NC}"
cd "$SCRIPT_DIR"

# Stop containers if they exist
if check_container "simple-orchestrator"; then
    echo "Stopping simple-orchestrator..."
    docker-compose -f simple-bots-compose.yml stop simple-orchestrator
fi

if check_container "simple-llm"; then
    echo "Stopping simple-llm..."
    docker-compose -f simple-bots-compose.yml stop simple-llm
fi

# Remove containers to ensure clean start
echo -e "${YELLOW}🗑️  Removing old containers...${NC}"
docker-compose -f simple-bots-compose.yml down --remove-orphans

# Build and start the bots
echo -e "${BLUE}🏗️  Building simple bot images...${NC}"
docker-compose -f simple-bots-compose.yml build --no-cache

echo -e "${BLUE}🚀 Starting simple bots...${NC}"
docker-compose -f simple-bots-compose.yml up -d

# Wait for containers to be healthy
echo -e "${BLUE}⏳ Waiting for bots to be ready...${NC}"

if wait_for_healthy "simple-orchestrator" && wait_for_healthy "simple-llm"; then
    echo -e "${GREEN}✅ Simple bots deployed successfully!${NC}"
    echo
    echo -e "${BLUE}🤖 Bot Information:${NC}"
    echo "===================="
    echo -e "Orchestrator: ${GREEN}@unmolded8581:acebuddy.quest${NC}"
    echo -e "LLM Bot:      ${GREEN}@subatomic6140:acebuddy.quest${NC}"
    echo
    echo -e "${BLUE}📍 Target Rooms:${NC}"
    echo "=================="
    echo "Room 1 (LLM):     !KyOMcaXNWvZvGgPqmw:acebuddy.quest"
    echo "Room 2 (Weather): !aJySTGOBquzIVrrcTB:acebuddy.quest"
    echo
    echo -e "${BLUE}💬 How to Use:${NC}"
    echo "=============="
    echo "1. Type 'das' or 'Das' in either room"
    echo "2. Orchestrator will acknowledge and call LLM bot"
    echo "3. LLM bot will respond and help"
    echo "4. Watch them be friendly buddies! 🤝"
    echo
    echo -e "${YELLOW}📝 View logs with:${NC}"
    echo "docker logs simple-orchestrator"
    echo "docker logs simple-llm"

else
    echo -e "${RED}❌ Failed to deploy simple bots${NC}"
    echo
    echo -e "${YELLOW}Check logs for errors:${NC}"
    echo "docker logs simple-orchestrator"
    echo "docker logs simple-llm"
    exit 1
fi

# Show running containers
echo
echo -e "${BLUE}🐳 Running Containers:${NC}"
echo "======================"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(simple-orchestrator|simple-llm|NAMES)"

echo
echo -e "${GREEN}🎉 Simple buddy bots are ready to chat!${NC}"
