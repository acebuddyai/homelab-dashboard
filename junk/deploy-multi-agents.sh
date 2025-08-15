#!/bin/bash
# =============================================================================
# MULTI-AGENT MATRIX SYSTEM DEPLOYMENT SCRIPT
# =============================================================================
# This script deploys the multi-agent Matrix system incrementally
# =============================================================================

set -e  # Exit on any error

echo "🤖 Starting Multi-Agent Matrix System Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found in homelab directory!${NC}"
    echo "   Please run ./fix-security-issues.sh first to create environment file."
    exit 1
fi

echo -e "${BLUE}📋 Environment file found. Loading variables...${NC}"
export $(grep -v "^#" .env | xargs)

# Verify critical variables for multi-agent system
required_vars=(
    "DOMAIN"
    "MATRIX_DOMAIN"
    "MATRIX_DB_PASSWORD"
    "ORCHESTRATOR_PASSWORD"
    "LLM_AGENT_PASSWORD"
    "COORDINATION_ROOM_ID"
)
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}❌ Error: Missing required environment variables:${NC}"
    printf "   - %s\n" "${missing_vars[@]}"
    echo ""
    echo -e "${YELLOW}💡 Run ./fix-security-issues.sh to generate missing variables${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required environment variables are set${NC}"
echo ""

# Function to check if container is running
check_container() {
    local container_name=$1
    if docker ps --format 'table {{.Names}}' | grep -q "^${container_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service health
wait_for_health() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    echo -e "${BLUE}   ⏳ Waiting for ${service_name} to become healthy...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if docker ps --filter "name=${service_name}" --filter "health=healthy" | grep -q "${service_name}"; then
            echo -e "${GREEN}   ✅ ${service_name} is healthy${NC}"
            return 0
        fi

        echo -e "${YELLOW}   ⏳ Attempt ${attempt}/${max_attempts} - waiting for ${service_name}...${NC}"
        sleep 10
        attempt=$((attempt + 1))
    done

    echo -e "${RED}   ❌ ${service_name} failed to become healthy after ${max_attempts} attempts${NC}"
    return 1
}

# Function to create Matrix user account
create_matrix_user() {
    local username=$1
    local password=$2
    local admin_flag=${3:-""}

    echo -e "${BLUE}   👤 Creating Matrix user: ${username}${NC}"

    # Check if user already exists
    if docker exec matrix-synapse register_new_matrix_user \
        -u "${username}" \
        -p "${password}" \
        ${admin_flag} \
        -c /data/homeserver.yaml 2>/dev/null; then
        echo -e "${GREEN}   ✅ User ${username} created successfully${NC}"
    else
        echo -e "${YELLOW}   ⚠️  User ${username} might already exist${NC}"
    fi
}

# Function to create Matrix room
create_matrix_room() {
    local room_alias=$1
    local room_name=$2

    echo -e "${BLUE}   🏠 Creating Matrix room: ${room_alias}${NC}"

    # This would typically be done via Matrix admin API or client
    # For now, we'll note that rooms need to be created manually
    echo -e "${YELLOW}   📝 Room ${room_alias} needs to be created manually via Matrix client${NC}"
}

echo -e "${BLUE}🎯 Phase 1: Checking Core Infrastructure${NC}"
echo "==========================================="

# Check if core Matrix services are running
if ! check_container "matrix-synapse"; then
    echo -e "${RED}❌ Matrix Synapse is not running${NC}"
    echo "   Please start Matrix services first:"
    echo "   cd matrix && docker-compose up -d"
    exit 1
fi

if ! check_container "ollama"; then
    echo -e "${RED}❌ Ollama is not running${NC}"
    echo "   Please start AI services first:"
    echo "   cd services && docker-compose -f ai-stack.yml up -d"
    exit 1
fi

echo -e "${GREEN}✅ Core infrastructure is running${NC}"
echo ""

echo -e "${BLUE}🔧 Phase 2: Prepare Multi-Agent Infrastructure${NC}"
echo "=============================================="

# Create bot user accounts
echo -e "${BLUE}📝 Creating bot user accounts...${NC}"

create_matrix_user "orchestrator" "${ORCHESTRATOR_PASSWORD}" "-a"
create_matrix_user "llm" "${LLM_AGENT_PASSWORD}"
create_matrix_user "search" "${SEARCH_AGENT_PASSWORD}"
create_matrix_user "rag" "${RAG_AGENT_PASSWORD}"

echo ""

# Deploy supporting services
echo -e "${BLUE}🚀 Deploying supporting services...${NC}"

# Deploy SearXNG for search capabilities
echo -e "${BLUE}   🔍 Deploying SearXNG...${NC}"
if ! check_container "searxng"; then
    # Create SearXNG configuration
    mkdir -p matrix/searxng
    cat > matrix/searxng/settings.yml << 'EOF'
use_default_settings: true
server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "replace-this-with-a-secret-key"
search:
  safe_search: 0
  autocomplete: ""
engines:
  - name: google
    disabled: false
  - name: bing
    disabled: false
  - name: duckduckgo
    disabled: false
EOF

    docker run -d \
        --name searxng \
        --network homelab \
        --ip 172.20.0.35 \
        -v "$(pwd)/matrix/searxng:/etc/searxng:rw" \
        -e BASE_URL="http://searxng:8080" \
        -e INSTANCE_NAME="Homelab Search" \
        --restart unless-stopped \
        searxng/searxng:latest

    echo -e "${GREEN}   ✅ SearXNG deployed${NC}"
else
    echo -e "${GREEN}   ✅ SearXNG already running${NC}"
fi

# Deploy Qdrant for vector database
echo -e "${BLUE}   🗄️  Deploying Qdrant vector database...${NC}"
if ! check_container "qdrant"; then
    docker run -d \
        --name qdrant \
        --network homelab \
        --ip 172.20.0.36 \
        -p 6333:6333 \
        -p 6334:6334 \
        -v qdrant_storage:/qdrant/storage \
        -e QDRANT__SERVICE__HTTP_PORT=6333 \
        -e QDRANT__SERVICE__GRPC_PORT=6334 \
        --restart unless-stopped \
        qdrant/qdrant:latest

    echo -e "${GREEN}   ✅ Qdrant deployed${NC}"
else
    echo -e "${GREEN}   ✅ Qdrant already running${NC}"
fi

# Deploy Redis for coordination
echo -e "${BLUE}   🔴 Deploying Redis for agent coordination...${NC}"
if ! check_container "matrix-redis"; then
    docker run -d \
        --name matrix-redis \
        --network homelab \
        --ip 172.20.0.37 \
        -v redis_data:/data \
        --restart unless-stopped \
        redis:7-alpine redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

    echo -e "${GREEN}   ✅ Redis deployed${NC}"
else
    echo -e "${GREEN}   ✅ Redis already running${NC}"
fi

echo ""

echo -e "${BLUE}🤖 Phase 3: Deploy Multi-Agent System${NC}"
echo "======================================"

# Build agent images
echo -e "${BLUE}🔨 Building agent Docker images...${NC}"

cd matrix/bot

# Build orchestrator
echo -e "${BLUE}   🏗️  Building orchestrator agent...${NC}"
docker build -f Dockerfile.orchestrator -t homelab/orchestrator:latest .

# Build LLM agent
echo -e "${BLUE}   🏗️  Building LLM agent...${NC}"
docker build -f Dockerfile.llm -t homelab/llm-agent:latest .

echo -e "${GREEN}✅ Agent images built successfully${NC}"

# Deploy orchestrator agent
echo -e "${BLUE}🎯 Deploying orchestrator agent...${NC}"
if check_container "matrix-orchestrator"; then
    echo -e "${YELLOW}   🔄 Stopping existing orchestrator...${NC}"
    docker stop matrix-orchestrator
    docker rm matrix-orchestrator
fi

docker run -d \
    --name matrix-orchestrator \
    --network homelab \
    --ip 172.20.0.26 \
    --env-file ../../.env \
    -e MATRIX_HOMESERVER_URL=http://matrix-synapse:8008 \
    -e MATRIX_BOT_USERNAME=@orchestrator:${MATRIX_DOMAIN} \
    -e MATRIX_BOT_PASSWORD=${ORCHESTRATOR_PASSWORD} \
    -e COORDINATION_ROOM_ID=${COORDINATION_ROOM_ID} \
    -e BOT_STORE_DIR=/app/store \
    -v orchestrator_store:/app/store \
    --restart unless-stopped \
    homelab/orchestrator:latest

echo -e "${GREEN}✅ Orchestrator agent deployed${NC}"

# Deploy LLM agent
echo -e "${BLUE}🧠 Deploying LLM agent...${NC}"
if check_container "matrix-llm-agent"; then
    echo -e "${YELLOW}   🔄 Stopping existing LLM agent...${NC}"
    docker stop matrix-llm-agent
    docker rm matrix-llm-agent
fi

docker run -d \
    --name matrix-llm-agent \
    --network homelab \
    --ip 172.20.0.27 \
    --env-file ../../.env \
    -e MATRIX_HOMESERVER_URL=http://matrix-synapse:8008 \
    -e MATRIX_BOT_USERNAME=@llm:${MATRIX_DOMAIN} \
    -e MATRIX_BOT_PASSWORD=${LLM_AGENT_PASSWORD} \
    -e COORDINATION_ROOM_ID=${COORDINATION_ROOM_ID} \
    -e BOT_STORE_DIR=/app/store \
    -e OLLAMA_URL=http://ollama:11434 \
    -e DEFAULT_LLM_MODEL=${DEFAULT_LLM_MODEL:-llama3.2:latest} \
    -e LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-2048} \
    -e LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.7} \
    -v llm_agent_store:/app/store \
    --restart unless-stopped \
    homelab/llm-agent:latest

echo -e "${GREEN}✅ LLM agent deployed${NC}"

cd ../../  # Return to homelab root

echo ""

echo -e "${BLUE}🏥 Phase 4: Health Checks${NC}"
echo "=========================="

# Wait for agents to start
sleep 15

# Check agent health
echo -e "${BLUE}🔍 Checking agent health...${NC}"

agents=("matrix-orchestrator" "matrix-llm-agent")
failed_agents=()

for agent in "${agents[@]}"; do
    if check_container "$agent"; then
        echo -e "${GREEN}   ✅ ${agent} is running${NC}"
    else
        echo -e "${RED}   ❌ ${agent} is not running${NC}"
        failed_agents+=("$agent")
    fi
done

# Check supporting services
services=("searxng" "qdrant" "matrix-redis")
for service in "${services[@]}"; do
    if check_container "$service"; then
        echo -e "${GREEN}   ✅ ${service} is running${NC}"
    else
        echo -e "${RED}   ❌ ${service} is not running${NC}"
        failed_agents+=("$service")
    fi
done

echo ""

if [ ${#failed_agents[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 Multi-Agent System Deployment Completed Successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 System Status:${NC}"
    echo "   - Orchestrator Agent: https://matrix.${MATRIX_DOMAIN}/ (as @orchestrator)"
    echo "   - LLM Agent: Integrated with Ollama at http://ollama:11434"
    echo "   - Search Service: SearXNG at http://searxng:8080"
    echo "   - Vector Database: Qdrant at http://qdrant:6333"
    echo "   - Coordination: Redis at redis://matrix-redis:6379"
    echo ""
    echo -e "${BLUE}🎯 Next Steps:${NC}"
    echo "1. 🏠 Create coordination room: ${COORDINATION_ROOM_ID}"
    echo "2. 👥 Invite all bots to the coordination room"
    echo "3. 🧪 Test agent communication:"
    echo "   !orchestrator help"
    echo "   !orchestrator agents"
    echo "   !orchestrator ask llm \"Hello from the orchestrator!\""
    echo "4. 🔗 Try agent chaining:"
    echo "   !orchestrator chain search->llm \"Find news about AI and summarize\""
    echo ""
    echo -e "${BLUE}🔧 Useful Commands:${NC}"
    echo "   - View orchestrator logs: docker logs -f matrix-orchestrator"
    echo "   - View LLM agent logs: docker logs -f matrix-llm-agent"
    echo "   - Check agent status: docker ps --filter network=homelab"
    echo "   - Stop all agents: docker stop matrix-orchestrator matrix-llm-agent"
    echo ""
    echo -e "${GREEN}✨ Your Multi-Agent Matrix System is ready!${NC}"
else
    echo -e "${RED}❌ Deployment completed with errors${NC}"
    echo -e "${YELLOW}Failed services:${NC}"
    printf "   - %s\n" "${failed_agents[@]}"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting:${NC}"
    echo "   - Check logs: docker logs <container_name>"
    echo "   - Verify environment variables in .env file"
    echo "   - Ensure Matrix and Ollama services are running"
    echo "   - Check network connectivity: docker network inspect homelab"
fi

echo ""
echo -e "${BLUE}📝 Manual Steps Required:${NC}"
echo "1. Create Matrix rooms using Element or another Matrix client:"
echo "   - Coordination room: #coordination:${MATRIX_DOMAIN}"
echo "   - Agent workspace: #agents:${MATRIX_DOMAIN}"
echo ""
echo "2. Invite bots to rooms:"
echo "   - @orchestrator:${MATRIX_DOMAIN}"
echo "   - @llm:${MATRIX_DOMAIN}"
echo ""
echo "3. Update COORDINATION_ROOM_ID in .env with actual room ID"
echo ""
echo -e "${YELLOW}⚠️  Remember to restart agents after updating room IDs${NC}"
