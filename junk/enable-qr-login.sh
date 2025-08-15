#!/bin/bash
# =============================================================================
# ENABLE QR CODE LOGIN FOR MATRIX - MAS Setup Script
# =============================================================================
# This script enables Matrix Authentication Service (MAS) to support QR code
# login and advanced authentication features for your Matrix homeserver.
# =============================================================================

set -e  # Exit on any error

echo "🔐 Enabling QR Code Login for Matrix Homeserver"
echo "=============================================="
echo ""

# Check if we're in the homelab directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "matrix" ]; then
    echo "❌ Error: This script must be run from the homelab directory!"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: docker-compose.yml, matrix/ directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please ensure your .env file contains the required MAS variables."
    exit 1
fi

echo "📋 Step 1: Checking prerequisites..."

# Check if MAS is currently disabled
if [ -d "mas.disabled" ] && [ ! -d "mas" ]; then
    echo "✅ Found disabled MAS directory - will enable it"
    MAS_DISABLED=true
elif [ -d "mas" ]; then
    echo "✅ MAS directory already exists"
    MAS_DISABLED=false
else
    echo "❌ Error: Neither mas/ nor mas.disabled/ directory found!"
    exit 1
fi

echo ""
echo "📋 Step 2: Backing up current Matrix configuration..."

# Backup current homeserver.yaml
cp matrix/synapse/homeserver.yaml matrix/synapse/homeserver.yaml.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backed up homeserver.yaml"

echo ""
echo "📋 Step 3: Enabling MAS..."

if [ "$MAS_DISABLED" = true ]; then
    # Move mas.disabled to mas
    echo "   Moving mas.disabled to mas..."
    mv mas.disabled mas
    echo "✅ MAS directory enabled"
fi

# Check if MAS config exists and is valid
if [ ! -f "mas/config.yaml" ]; then
    echo "❌ Error: mas/config.yaml not found!"
    echo "   Please ensure MAS configuration exists."
    exit 1
fi

echo ""
echo "📋 Step 4: Updating Matrix configuration for MAS integration..."

# Create the updated homeserver.yaml with MAS integration
cat >> matrix/synapse/homeserver.yaml << 'EOF'

# =============================================================================
# MAS (Matrix Authentication Service) Integration for QR Code Login
# =============================================================================

# OIDC Configuration for MAS integration
experimental_features:
  # MSC3861: Matrix authentication via OIDC
  msc3861:
    issuer: https://auth.acebuddy.quest/
    client_id: "0000000000000000000SYNAPSE"
    client_auth_method: client_secret_basic
    client_secret: "${SYNAPSE_CLIENT_SECRET}"
    admin_token: "${MAS_ADMIN_TOKEN}"
    account_management_url: https://auth.acebuddy.quest/account/

  # MSC4108: QR Code Login
  msc4108_enabled: true
  msc4108_delegation_endpoint: https://auth.acebuddy.quest/login/qr

  # MSC3882: Login token request
  msc3882_enabled: true
  msc3882_ui_auth: false

  # MSC3886: Simple login
  msc3886_endpoint: "/login/qr"

# Disable local password authentication (MAS will handle it)
password_config:
  enabled: false

# Disable local registration (MAS will handle it)
enable_registration: false

# Email verification handled by MAS
registrations_require_3pid: []

EOF

echo "✅ Updated Matrix configuration for MAS integration"

echo ""
echo "📋 Step 5: Adding MAS route to Caddy..."

# Add MAS route to Caddyfile if not already present
if ! grep -q "auth.acebuddy.quest" caddy/Caddyfile; then
    cat >> caddy/Caddyfile << 'EOF'

# Matrix Authentication Service
auth.acebuddy.quest {
    reverse_proxy matrix-auth-service:8080
}
EOF
    echo "✅ Added MAS route to Caddyfile"
else
    echo "✅ MAS route already exists in Caddyfile"
fi

echo ""
echo "📋 Step 6: Deploying MAS..."

# Deploy MAS
cd mas
echo "   Starting MAS services..."
docker-compose up -d

# Wait for services to start
echo "   Waiting for services to become healthy..."
sleep 15

# Check if MAS is healthy
echo "   Checking MAS health..."
if docker exec matrix-auth-service wget --spider -q http://localhost:8081/health 2>/dev/null; then
    echo "✅ MAS health check passed"
else
    echo "⚠️  MAS health check failed (may still be starting up)"
fi

cd ..

echo ""
echo "📋 Step 7: Restarting Matrix with MAS integration..."

# Restart Matrix services
cd matrix
docker-compose restart
cd ..

# Reload Caddy configuration
echo "   Reloading Caddy configuration..."
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

echo ""
echo "📋 Step 8: Verifying setup..."

sleep 10

# Check service health
echo "🏥 Service Health Check:"
services=("matrix-synapse" "matrix-auth-service" "matrix-postgres" "mas-postgres" "caddy")

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo "   ✅ $service: Running"
    else
        echo "   ❌ $service: Not running"
    fi
done

echo ""
echo "🎉 QR Code Login Setup Complete!"
echo ""
echo "🔗 Service URLs:"
echo "   Matrix Chat:    https://cinny.acebuddy.quest"
echo "   Matrix Auth:    https://auth.acebuddy.quest"
echo "   Matrix API:     https://matrix.acebuddy.quest"
echo "   Status Page:    https://status.acebuddy.quest"
echo ""
echo "📱 QR Code Login Usage:"
echo "   1. Open Matrix client (Element, Cinny, etc.)"
echo "   2. Go to Login → QR Code Login"
echo "   3. Scan QR code with another signed-in device"
echo "   4. Verify and complete login"
echo ""
echo "🧪 Testing Commands:"
echo "   # Test MAS health"
echo "   curl https://auth.acebuddy.quest/health"
echo ""
echo "   # Test Matrix with MAS"
echo "   curl https://matrix.acebuddy.quest/_matrix/client/versions"
echo ""
echo "   # View MAS logs"
echo "   docker logs -f matrix-auth-service"
echo ""
echo "   # Test email (still works)"
echo "   cd matrix && python3 test-email.py --email your@email.com"
echo ""
echo "⚠️  Important Notes:"
echo "   - Existing user sessions may need to re-login"
echo "   - Password authentication now handled by MAS"
echo "   - QR login requires compatible Matrix clients"
echo "   - Email functionality preserved through MAS"
echo ""
echo "🔄 To disable QR login and revert to basic auth:"
echo "   ./disable-qr-login.sh"
echo ""
echo "✨ Your Matrix server now supports QR code login!"
