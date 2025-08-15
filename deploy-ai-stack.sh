#!/bin/bash

# Deployment script for Homelab AI Stack
# This script cleanly transitions from Matrix to the new AI architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="acebuddy.quest"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Homelab AI Stack Deployment${NC}"
echo -e "${BLUE}   Domain: ${DOMAIN}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Stop Matrix services
echo -e "${YELLOW}Step 1: Stopping Matrix services...${NC}"
docker stop matrix-cinny matrix-bot matrix-llm-agent matrix-orchestrator matrix-synapse matrix-postgres matrix-redis 2>/dev/null || true
docker rm matrix-cinny matrix-bot matrix-llm-agent matrix-orchestrator matrix-synapse matrix-postgres matrix-redis 2>/dev/null || true
echo -e "${GREEN}✓ Matrix services stopped${NC}"

# Step 2: Keep existing services running
echo -e "${YELLOW}Step 2: Verifying existing services...${NC}"
services_to_keep=("ollama" "open-webui" "nextcloud" "nextcloud-db" "vikunja" "caddy" "homelab-status")
for service in "${services_to_keep[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        echo -e "${GREEN}✓ ${service} is running${NC}"
    else
        echo -e "${RED}✗ ${service} is not running${NC}"
    fi
done

# Step 3: Deploy new services
echo -e "${YELLOW}Step 3: Deploying new AI stack...${NC}"

# Start only the new services that aren't already running
docker-compose -f docker-compose-ai-stack.yml up -d \
    windmill-db \
    windmill-server \
    windmill-worker \
    redis \
    api-gateway \
    web-ui

echo -e "${GREEN}✓ New services deployed${NC}"

# Step 4: Wait for services to be ready
echo -e "${YELLOW}Step 4: Waiting for services to be ready...${NC}"
sleep 10

# Check Windmill database
echo -n "Checking Windmill DB... "
for i in {1..30}; do
    if docker exec windmill-db pg_isready -U windmill >/dev/null 2>&1; then
        echo -e "${GREEN}Ready${NC}"
        break
    fi
    sleep 2
done

# Check Redis
echo -n "Checking Redis... "
if docker exec redis redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}Ready${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Check Qdrant (already running)
echo -n "Checking Qdrant... "
if curl -s http://localhost:6333/health >/dev/null 2>&1; then
    echo -e "${GREEN}Ready${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Step 5: Initialize Qdrant collections
echo -e "${YELLOW}Step 5: Initializing vector database...${NC}"

# Create knowledge_base collection
curl -s -X PUT "http://localhost:6333/collections/knowledge_base" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' >/dev/null 2>&1 && echo -e "${GREEN}✓ knowledge_base collection created${NC}" || echo -e "${YELLOW}⚠ knowledge_base already exists${NC}"

# Create tasks collection
curl -s -X PUT "http://localhost:6333/collections/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' >/dev/null 2>&1 && echo -e "${GREEN}✓ tasks collection created${NC}" || echo -e "${YELLOW}⚠ tasks already exists${NC}"

# Create briefings collection
curl -s -X PUT "http://localhost:6333/collections/briefings" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' >/dev/null 2>&1 && echo -e "${GREEN}✓ briefings collection created${NC}" || echo -e "${YELLOW}⚠ briefings already exists${NC}"

# Step 6: Update Caddy configuration
echo -e "${YELLOW}Step 6: Updating Caddy configuration...${NC}"
if [ -f caddy/Caddyfile.new ]; then
    cp caddy/Caddyfile caddy/Caddyfile.backup.$(date +%Y%m%d_%H%M%S)
    cp caddy/Caddyfile.new caddy/Caddyfile
    docker restart caddy
    echo -e "${GREEN}✓ Caddy configuration updated${NC}"
else
    echo -e "${RED}✗ caddy/Caddyfile.new not found${NC}"
fi

# Step 7: Download LLM models if needed
echo -e "${YELLOW}Step 7: Checking AI models...${NC}"
if docker exec ollama ollama list | grep -q "llama3.2:latest"; then
    echo -e "${GREEN}✓ llama3.2:latest already available${NC}"
else
    echo "Downloading llama3.2:latest (this may take a while)..."
    docker exec ollama ollama pull llama3.2:latest
fi

if docker exec ollama ollama list | grep -q "all-minilm:latest"; then
    echo -e "${GREEN}✓ all-minilm:latest already available${NC}"
else
    echo "Downloading all-minilm:latest..."
    docker exec ollama ollama pull all-minilm:latest
fi

# Step 8: Test endpoints
echo -e "${YELLOW}Step 8: Testing endpoints...${NC}"

# Test API Gateway
echo -n "Testing API Gateway... "
if curl -s http://localhost:3000/health >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Test Windmill
echo -n "Testing Windmill... "
if curl -s http://localhost:8000/api/version >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Test Web UI
echo -n "Testing Web UI... "
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Step 9: Display status
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Services Status:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "ollama|open-webui|windmill|qdrant|redis|api-gateway|web-ui|caddy|nextcloud|vikunja"

echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo "  Main AI Interface:  https://ai.${DOMAIN}"
echo "  Chat (Open WebUI):  https://chat.${DOMAIN}"
echo "  API Gateway:        https://api.${DOMAIN}"
echo "  Workflows:          https://workflows.${DOMAIN}"
echo "  Task Management:    https://tasks.${DOMAIN}"
echo "  File Storage:       https://files.${DOMAIN}"
echo "  Search Engine:      https://search.${DOMAIN}"
echo "  Status Page:        https://status.${DOMAIN}"
echo ""
echo -e "${YELLOW}Local Access (for testing):${NC}"
echo "  Web UI:            http://localhost:8080"
echo "  API Gateway:       http://localhost:3000"
echo "  Windmill:          http://localhost:8000"
echo "  Qdrant:            http://localhost:6333"
echo ""
echo -e "${BLUE}Default Credentials:${NC}"
echo "  Windmill: admin@windmill.dev / changeme"
echo "  (Change immediately at https://workflows.${DOMAIN})"
echo ""
echo -e "${GREEN}✨ Your AI Assistant is ready at https://ai.${DOMAIN} ✨${NC}"
