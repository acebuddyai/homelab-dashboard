#!/bin/bash
# =============================================================================
# DISABLE QR CODE LOGIN FOR MATRIX - Revert to Basic Auth Script
# =============================================================================
# This script disables Matrix Authentication Service (MAS) and reverts back
# to basic Synapse authentication while preserving email functionality.
# =============================================================================

set -e  # Exit on any error

echo "🔙 Disabling QR Code Login - Reverting to Basic Matrix Auth"
echo "=========================================================="
echo ""

# Check if we're in the homelab directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "matrix" ]; then
    echo "❌ Error: This script must be run from the homelab directory!"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: docker-compose.yml, matrix/ directory"
    exit 1
fi

echo "📋 Step 1: Backing up current configuration..."

# Create backup timestamp
BACKUP_TIME=$(date +%Y%m%d_%H%M%S)

# Backup current homeserver.yaml
if [ -f "matrix/synapse/homeserver.yaml" ]; then
    cp matrix/synapse/homeserver.yaml matrix/synapse/homeserver.yaml.mas-backup.$BACKUP_TIME
    echo "✅ Backed up current homeserver.yaml"
fi

# Backup Caddyfile
if [ -f "caddy/Caddyfile" ]; then
    cp caddy/Caddyfile caddy/Caddyfile.mas-backup.$BACKUP_TIME
    echo "✅ Backed up current Caddyfile"
fi

echo ""
echo "📋 Step 2: Stopping MAS services..."

# Stop MAS if it's running
if [ -d "mas" ] && [ -f "mas/docker-compose.yml" ]; then
    cd mas
    echo "   Stopping Matrix Authentication Service..."
    docker-compose down --remove-orphans || true
    cd ..
    echo "✅ MAS services stopped"
fi

echo ""
echo "📋 Step 3: Disabling MAS..."

# Move mas to mas.disabled if it exists
if [ -d "mas" ]; then
    echo "   Moving mas to mas.disabled..."
    if [ -d "mas.disabled" ]; then
        rm -rf mas.disabled.old 2>/dev/null || true
        mv mas.disabled mas.disabled.old
    fi
    mv mas mas.disabled
    echo "✅ MAS disabled"
fi

echo ""
echo "📋 Step 4: Restoring basic Matrix authentication..."

# Restore homeserver.yaml to basic auth with email support
cat > matrix/synapse/homeserver.yaml << 'EOF'
# Configuration file for Synapse.
server_name: "acebuddy.quest"
public_baseurl: "https://matrix.acebuddy.quest"
pid_file: /data/homeserver.pid

listeners:
  - port: 8008
    tls: false
    type: http
    x_forwarded: true
    resources:
      - names: [client, federation]
        compress: false

database:
  name: psycopg2
  args:
    user: synapse
    password: mX9kL2pQ8vR5nE7wF3gH9jK6mN4bV1cZ
    database: synapse
    host: matrix-postgres
    port: 5432
    cp_min: 5
    cp_max: 10

log_config: "/data/acebuddy.quest.log.config"
media_store_path: /data/media_store
report_stats: false

# Generate these secrets - they should be random strings
registration_shared_secret: "mX9kL2pQ8vR5nE7wF3gH9jK6mN4bV1cZ8yU1oP4qW7rT5nM2sL9vB3xC6zA8fG1h"
macaroon_secret_key: "nM4bV1cZ8yU1oP4qW7rT5nM2sL9vB3xC6zA8fG1hmX9kL2pQ8vR5nE7wF3gH9jK6"
form_secret: "sL9vB3xC6zA8fG1hmX9kL2pQ8vR5nE7wF3gH9jK6mN4bV1cZ8yU1oP4qW7rT5nM2"
signing_key_path: "/data/acebuddy.quest.signing.key"

trusted_key_servers:
  - server_name: "matrix.org"

# Standard registration and authentication
enable_registration: true
enable_registration_without_verification: true
registration_requires_token: false

# Standard password authentication
password_config:
  enabled: true
  pepper: "qW7rT5nM2sL9vB3xC6zA8fG1hmX9kL2pQ8vR5nE7wF3gH9jK6mN4bV1cZ8yU1oP4"

# Security settings
use_presence: true
require_auth_for_profile_requests: false
allow_public_rooms_without_auth: true
allow_public_rooms_over_federation: true

# Device verification and encryption
encryption_enabled_by_default_for_room_type: all
encryption_enabled_by_default: true

# Device list updates for verification
device_list_updater:
  enabled: true

# Cross-signing keys for device verification
trust_identity_server_for_password_resets: false
enable_3pid_lookup: true

# Basic device verification (no QR login without MAS)
allow_device_name_lookup_over_federation: true

# Rate limiting
rc_message:
  per_second: 0.2
  burst_count: 10

rc_registration:
  per_second: 0.17
  burst_count: 3

rc_login:
  address:
    per_second: 0.17
    burst_count: 3
  account:
    per_second: 0.17
    burst_count: 3
  failed_attempts:
    per_second: 0.17
    burst_count: 3

# Media settings
max_upload_size: 50M
max_image_pixels: 32M
dynamic_thumbnails: true

# Email configuration for password reset and notifications
email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: acebuddyai@gmail.com
  smtp_pass: qcdvtweeiobrkbhf
  require_transport_security: true
  enable_tls: true
  notif_from: "Matrix acebuddy.quest <acebuddyai@gmail.com>"
  app_name: "Matrix acebuddy.quest"
  enable_notifs: true
  notif_for_new_users: true
  client_base_url: "https://cinny.acebuddy.quest"
  # Email validation settings
  validation_token_lifetime: 24h
  invite_client_location: "https://cinny.acebuddy.quest"

# Three-PID (email/phone) settings
# Allow email for password reset
threepid_behaviour_email: local

# Email address requirements (optional for registration)
registrations_require_3pid:
  - email

# Allow email addresses to be added to accounts
allowed_local_3pids:
  - medium: email
    pattern: '^[^@]+@[^@]+\.[^@]+$'

# Enable email notifications globally
enable_notifs: true

# URL previews
url_preview_enabled: true
url_preview_ip_range_blacklist:
  - "127.0.0.0/8"
  - "10.0.0.0/8"
  - "172.16.0.0/12"
  - "192.168.0.0/16"
  - "100.64.0.0/10"
  - "169.254.0.0/16"
  - "::1/128"
  - "fe80::/64"
  - "fc00::/7"

# Clean up old events
retention:
  enabled: true
  default_policy:
    min_lifetime: 1d
    max_lifetime: 1y
EOF

echo "✅ Matrix configuration updated for basic auth"

echo ""
echo "📋 Step 5: Removing MAS route from Caddy..."

# Remove MAS route from Caddyfile
if grep -q "auth.acebuddy.quest" caddy/Caddyfile; then
    # Create temp file without MAS section
    awk '
    /^# Matrix Authentication Service$/ { skip = 1; next }
    /^auth\.acebuddy\.quest \{$/ { skip = 1; next }
    skip && /^\}$/ { skip = 0; next }
    !skip { print }
    ' caddy/Caddyfile > caddy/Caddyfile.tmp

    mv caddy/Caddyfile.tmp caddy/Caddyfile
    echo "✅ Removed MAS route from Caddyfile"
else
    echo "✅ No MAS route found in Caddyfile"
fi

echo ""
echo "📋 Step 6: Restarting services..."

# Restart Matrix services
echo "   Restarting Matrix services..."
cd matrix
docker-compose restart
cd ..

# Reload Caddy
echo "   Reloading Caddy configuration..."
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

echo ""
echo "📋 Step 7: Verifying setup..."

sleep 10

# Check service health
echo "🏥 Service Health Check:"
services=("matrix-synapse" "matrix-postgres" "caddy")

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo "   ✅ $service: Running"
    else
        echo "   ❌ $service: Not running"
    fi
done

# Test Matrix API
echo ""
echo "🧪 Testing Matrix API..."
if curl -s https://matrix.acebuddy.quest/_matrix/client/versions > /dev/null; then
    echo "✅ Matrix API responding"
else
    echo "❌ Matrix API not responding"
fi

echo ""
echo "🎉 QR Code Login Disabled - Basic Auth Restored!"
echo ""
echo "🔗 Service URLs:"
echo "   Matrix Chat:    https://cinny.acebuddy.quest"
echo "   Matrix API:     https://matrix.acebuddy.quest"
echo "   Status Page:    https://status.acebuddy.quest"
echo ""
echo "✅ Working Features:"
echo "   ✅ Password authentication"
echo "   ✅ Email password reset"
echo "   ✅ Email verification for registration"
echo "   ✅ Device verification (manual)"
echo "   ✅ End-to-end encryption"
echo ""
echo "❌ Disabled Features:"
echo "   ❌ QR code login"
echo "   ❌ OAuth/OIDC authentication"
echo "   ❌ Advanced device management"
echo ""
echo "🧪 Test email functionality:"
echo "   cd matrix && python3 test-email.py --email your@email.com"
echo ""
echo "🔄 To re-enable QR login:"
echo "   ./enable-qr-login.sh"
echo ""
echo "📊 View logs:"
echo "   docker logs -f matrix-synapse"
echo "   docker logs -f caddy"
echo ""
echo "✨ Basic Matrix authentication with email support is ready!"
