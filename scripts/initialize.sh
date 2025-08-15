#!/bin/bash

# Initialize Homelab AI Assistant
# This script sets up the initial configuration after deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:3000}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
WINDMILL_URL="${WINDMILL_URL:-http://localhost:8000}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if service is ready
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    print_color "$YELLOW" "⏳ Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_color "$GREEN" "✓ $service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_color "$RED" "✗ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Header
echo ""
print_color "$BLUE" "╔══════════════════════════════════════════════╗"
print_color "$BLUE" "║     Homelab AI Assistant Initialization     ║"
print_color "$BLUE" "╚══════════════════════════════════════════════╝"
echo ""

# Step 1: Check prerequisites
print_color "$BLUE" "📋 Step 1: Checking prerequisites..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_color "$RED" "✗ Docker is not running. Please start Docker first."
    exit 1
fi
print_color "$GREEN" "✓ Docker is running"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_color "$RED" "✗ docker-compose is not installed"
    exit 1
fi
print_color "$GREEN" "✓ docker-compose is installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_color "$RED" "✗ .env file not found. Run ./scripts/generate-passwords.sh first"
    exit 1
fi
print_color "$GREEN" "✓ .env file exists"

# Step 2: Check if services are running
print_color "$BLUE" "\n📦 Step 2: Checking services..."

services=("ollama" "windmill-server" "windmill-worker" "windmill-db" "qdrant" "redis" "searxng" "api-gateway")
all_running=true

for service in "${services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        print_color "$GREEN" "✓ $service is running"
    else
        print_color "$YELLOW" "⚠ $service is not running"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    print_color "$YELLOW" "\n⚠ Some services are not running. Starting them now..."
    docker-compose -f docker-compose-ai-stack.yml up -d
    sleep 10
fi

# Step 3: Wait for services to be ready
print_color "$BLUE" "\n🔄 Step 3: Waiting for services to be ready..."

wait_for_service "API Gateway" "$API_URL/health"
wait_for_service "Qdrant" "$QDRANT_URL/health"
wait_for_service "Windmill" "$WINDMILL_URL/api/version"

# Step 4: Initialize Qdrant collections
print_color "$BLUE" "\n🗄️ Step 4: Initializing vector database collections..."

# Create knowledge_base collection
print_color "$YELLOW" "Creating knowledge_base collection..."
curl -s -X PUT "$QDRANT_URL/collections/knowledge_base" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "default_segment_number": 2
    },
    "replication_factor": 1
  }' > /dev/null 2>&1 && print_color "$GREEN" "✓ knowledge_base collection created" || print_color "$YELLOW" "⚠ knowledge_base collection already exists"

# Create tasks collection
print_color "$YELLOW" "Creating tasks collection..."
curl -s -X PUT "$QDRANT_URL/collections/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' > /dev/null 2>&1 && print_color "$GREEN" "✓ tasks collection created" || print_color "$YELLOW" "⚠ tasks collection already exists"

# Create briefings collection
print_color "$YELLOW" "Creating briefings collection..."
curl -s -X PUT "$QDRANT_URL/collections/briefings" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' > /dev/null 2>&1 && print_color "$GREEN" "✓ briefings collection created" || print_color "$YELLOW" "⚠ briefings collection already exists"

# Create conversations collection
print_color "$YELLOW" "Creating conversations collection..."
curl -s -X PUT "$QDRANT_URL/collections/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }' > /dev/null 2>&1 && print_color "$GREEN" "✓ conversations collection created" || print_color "$YELLOW" "⚠ conversations collection already exists"

# Step 5: Download LLM models
print_color "$BLUE" "\n🤖 Step 5: Downloading AI models..."

# Check if Ollama container is running
if docker ps --format '{{.Names}}' | grep -q "^ollama$"; then
    # Pull default model
    print_color "$YELLOW" "Downloading llama3.2:latest (this may take a while)..."
    if docker exec ollama ollama pull llama3.2:latest 2>/dev/null; then
        print_color "$GREEN" "✓ llama3.2:latest downloaded"
    else
        print_color "$YELLOW" "⚠ llama3.2:latest already exists or download failed"
    fi

    # Pull embedding model
    print_color "$YELLOW" "Downloading all-minilm:latest..."
    if docker exec ollama ollama pull all-minilm:latest 2>/dev/null; then
        print_color "$GREEN" "✓ all-minilm:latest downloaded"
    else
        print_color "$YELLOW" "⚠ all-minilm:latest already exists or download failed"
    fi

    # List available models
    print_color "$YELLOW" "\nAvailable models:"
    docker exec ollama ollama list
else
    print_color "$RED" "✗ Ollama container is not running. Skipping model download."
fi

# Step 6: Initialize Windmill
print_color "$BLUE" "\n⚙️ Step 6: Initializing Windmill..."

# Check if Windmill is accessible
if curl -s -f "$WINDMILL_URL/api/version" > /dev/null 2>&1; then
    print_color "$GREEN" "✓ Windmill is accessible"

    # Create workspace if needed (this might require authentication)
    print_color "$YELLOW" "Note: You may need to manually configure Windmill at $WINDMILL_URL"
    print_color "$YELLOW" "Default credentials: admin@windmill.dev / changeme"
else
    print_color "$RED" "✗ Windmill is not accessible. Please check the service."
fi

# Step 7: Initialize Redis
print_color "$BLUE" "\n💾 Step 7: Initializing Redis cache..."

if docker exec redis redis-cli ping > /dev/null 2>&1; then
    print_color "$GREEN" "✓ Redis is responding"

    # Set initial configuration
    docker exec redis redis-cli CONFIG SET maxmemory 512mb > /dev/null 2>&1
    docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru > /dev/null 2>&1
    print_color "$GREEN" "✓ Redis configured with 512MB memory limit and LRU eviction"
else
    print_color "$RED" "✗ Redis is not responding"
fi

# Step 8: Setup SearXNG
print_color "$BLUE" "\n🔍 Step 8: Configuring SearXNG..."

# Create SearXNG configuration directory if it doesn't exist
if [ ! -d "./searxng" ]; then
    mkdir -p ./searxng
    print_color "$GREEN" "✓ Created SearXNG configuration directory"
fi

# Create basic SearXNG settings if not exists
if [ ! -f "./searxng/settings.yml" ]; then
    cat > ./searxng/settings.yml << 'EOF'
general:
  instance_name: "Homelab Search"
  contact_url: false
  enable_metrics: false

search:
  safe_search: 1
  autocomplete: "duckduckgo"
  default_lang: "en"
  max_page: 5

server:
  secret_key: "${SEARXNG_SECRET}"
  limiter: true
  image_proxy: true

ui:
  default_theme: simple
  theme_args:
    simple_style: dark

engines:
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
  - name: google
    engine: google
    shortcut: g
  - name: wikipedia
    engine: wikipedia
    shortcut: wiki
  - name: github
    engine: github
    shortcut: gh
  - name: stackoverflow
    engine: stackoverflow
    shortcut: so
EOF
    print_color "$GREEN" "✓ Created SearXNG configuration"
fi

# Step 9: Create initial data
print_color "$BLUE" "\n📚 Step 9: Creating initial data..."

# Add a welcome document to knowledge base
print_color "$YELLOW" "Adding welcome document to knowledge base..."
curl -s -X POST "$API_URL/api/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "knowledge_base",
    "documents": [{
      "text": "Welcome to your Homelab AI Assistant! This system combines local LLMs, workflow automation, and knowledge management to create your personal AI operating system. Key features include: RAG-powered knowledge base, task automation, daily briefings, and web search capabilities.",
      "title": "Welcome Guide",
      "source": "system",
      "metadata": {
        "type": "documentation",
        "created_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
      }
    }]
  }' > /dev/null 2>&1 && print_color "$GREEN" "✓ Welcome document added" || print_color "$YELLOW" "⚠ Failed to add welcome document"

# Step 10: Health check
print_color "$BLUE" "\n🏥 Step 10: Running health check..."

# Check all endpoints
endpoints=(
    "$API_URL/health:API Gateway"
    "$QDRANT_URL/health:Qdrant"
    "$WINDMILL_URL/api/version:Windmill"
)

all_healthy=true
for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint"
    if curl -s -f "$url" > /dev/null 2>&1; then
        print_color "$GREEN" "✓ $name is healthy"
    else
        print_color "$RED" "✗ $name is not responding"
        all_healthy=false
    fi
done

# Step 11: Display summary
echo ""
print_color "$BLUE" "╔══════════════════════════════════════════════╗"
print_color "$BLUE" "║           Initialization Complete           ║"
print_color "$BLUE" "╚══════════════════════════════════════════════╝"
echo ""

if [ "$all_healthy" = true ]; then
    print_color "$GREEN" "🎉 System initialized successfully!"
    echo ""
    print_color "$BLUE" "📌 Access Points:"
    echo "  • Web UI: http://localhost:8080"
    echo "  • API Gateway: http://localhost:3000"
    echo "  • Windmill: http://localhost:8000"
    echo "  • OpenWebUI: http://localhost:8080"
    echo ""
    print_color "$BLUE" "📚 Next Steps:"
    echo "  1. Open the Web UI in your browser"
    echo "  2. Configure your preferences in Settings"
    echo "  3. Try the AI Chat feature"
    echo "  4. Upload documents to Knowledge Base"
    echo "  5. Create your first task"
    echo "  6. Explore workflow automation"
    echo ""
    print_color "$YELLOW" "💡 Tip: Run './scripts/health-check.sh' anytime to check system status"
else
    print_color "$YELLOW" "⚠️ System initialized with warnings"
    echo ""
    print_color "$YELLOW" "Some services may not be fully operational."
    print_color "$YELLOW" "Check the logs with: docker-compose -f docker-compose-ai-stack.yml logs"
fi

echo ""
print_color "$BLUE" "Thank you for using Homelab AI Assistant! 🚀"
echo ""
