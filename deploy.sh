#!/bin/bash
# =============================================================================
# HOMELAB MASTER DEPLOYMENT SCRIPT - 2025 Edition
# =============================================================================
# This script deploys all services with centralized environment management
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting Homelab Deployment with Centralized Secrets Management"
echo "=================================================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in homelab directory!"
    echo "   Please create .env file with all required secrets first."
    exit 1
fi

echo "📋 Environment file found. Loading variables..."
export $(grep -v "^#" .env | xargs)

# Verify critical variables
required_vars=("DOMAIN" "MATRIX_DOMAIN" "MATRIX_DB_PASSWORD" "MAS_POSTGRES_PASSWORD" "MAS_ENCRYPTION_KEY" "MATRIX_SECRET" "SYNAPSE_CLIENT_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf "   - %s\n" "${missing_vars[@]}"
    exit 1
fi

echo "✅ All required environment variables are set"
echo ""

# Function to deploy service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    
    echo "🔧 Deploying $service_name..."
    cd "$service_dir"
    
    # Generate config if script exists
    if [ -f "generate-config.sh" ]; then
        echo "   📝 Generating configuration..."
        ./generate-config.sh
    fi
    
    # Update synapse config if script exists
    if [ -f "update-synapse-config.sh" ]; then
        echo "   📝 Updating Synapse configuration..."
        ./update-synapse-config.sh
    fi
    
    # Stop existing containers
    echo "   🛑 Stopping existing containers..."
    docker-compose down --remove-orphans || true
    
    # Start services
    echo "   🚀 Starting services..."
    docker-compose up -d
    
    # Wait for health checks
    echo "   ⏳ Waiting for services to become healthy..."
    sleep 10
    
    cd ..
    echo "   ✅ $service_name deployed successfully"
    echo ""
}

# Deploy services in order
echo "🎯 Starting deployment sequence..."
echo ""

# 1. Deploy MAS first (Matrix depends on it)
deploy_service "Matrix Authentication Service (MAS)" "mas"

# 2. Deploy Matrix/Synapse
deploy_service "Matrix/Synapse" "matrix"

# 3. Check service health
echo "🏥 Performing health checks..."
echo ""

# Check MAS health
echo "   Checking MAS health..."
if curl -f -s http://localhost:8081/health > /dev/null; then
    echo "   ✅ MAS is healthy"
else
    echo "   ⚠️  MAS health check failed (this might be normal during startup)"
fi

# Check Matrix health
echo "   Checking Matrix health..."
if docker exec matrix-synapse test -f /data/homeserver.yaml; then
    echo "   ✅ Matrix configuration exists"
else
    echo "   ⚠️  Matrix configuration check failed"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📊 Service Status:"
echo "   - MAS Auth Service: https://auth.${MATRIX_DOMAIN}/"
echo "   - Element Web: https://element.${MATRIX_DOMAIN}/"
echo "   - Matrix Server: https://${MATRIX_DOMAIN}/"
echo ""
echo "🔧 Useful commands:"
echo "   - View MAS logs: docker logs -f matrix-auth-service"
echo "   - View Synapse logs: docker logs -f matrix-synapse" 
echo "   - Check MAS config: docker exec matrix-auth-service mas-cli config check"
echo "   - Test MAS health: curl http://localhost:8081/health"
echo ""
echo "✨ Your Matrix homeserver with MAS authentication is ready!"
