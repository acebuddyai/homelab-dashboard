#!/bin/bash
# Nextcloud Setup and Initialization Script
# This script performs a fresh installation of Nextcloud with all optimizations

set -e

echo "🚀 Starting Nextcloud Fresh Installation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running from the correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the nextcloud directory"
    exit 1
fi

# Step 1: Clean up old volumes
print_status "Cleaning up old Nextcloud volumes..."
docker-compose down -v 2>/dev/null || true
docker volume rm nextcloud_nextcloud_db nextcloud_nextcloud_data 2>/dev/null || true

# Step 2: Create environment file if it doesn't exist
if [ ! -f "../.env" ]; then
    print_status "Creating environment file..."
    cat > ../.env << 'EOF'
# Nextcloud Database
NEXTCLOUD_DB_PASSWORD=nc_db_$(openssl rand -hex 16)

# Redis Password
REDIS_PASSWORD=redis_$(openssl rand -hex 16)

# Nextcloud Admin
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=admin_$(openssl rand -hex 16)

# Collabora
COLLABORA_USERNAME=admin
COLLABORA_PASSWORD=collabora_$(openssl rand -hex 16)

# Default Phone Region (use your country code)
DEFAULT_PHONE_REGION=US

# SMTP Settings (update these with your email provider)
SMTP_HOST=mail.acebuddy.quest
SMTP_PORT=587
SMTP_SECURE=tls
SMTP_USERNAME=your-email@acebuddy.quest
SMTP_PASSWORD=your-email-password
MAIL_FROM_ADDRESS=nextcloud
MAIL_DOMAIN=acebuddy.quest
EOF
    print_warning "Environment file created. Please update SMTP settings in ../.env"
fi

# Step 3: Update PHP configuration with Redis password
print_status "Updating PHP configuration..."
REDIS_PASS=$(grep REDIS_PASSWORD ../.env | cut -d '=' -f2)
sed -i "s|session.save_path = \"tcp://nextcloud-redis:6379?auth=redis_secure_password\"|session.save_path = \"tcp://nextcloud-redis:6379?auth=${REDIS_PASS}\"|" config/php.ini

# Step 4: Start services
print_status "Starting Nextcloud services..."
docker-compose up -d

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Wait for Nextcloud to be ready
print_status "Waiting for Nextcloud to initialize..."
until docker-compose exec -T nextcloud-app php -v &>/dev/null; do
    echo -n "."
    sleep 5
done
echo ""

# Step 5: Run Nextcloud initialization
print_status "Configuring Nextcloud..."

# Install Nextcloud if not already installed
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:install \
    --database="pgsql" \
    --database-name="nextcloud" \
    --database-host="nextcloud-db" \
    --database-user="nextcloud" \
    --database-pass="$(grep NEXTCLOUD_DB_PASSWORD ../.env | cut -d '=' -f2)" \
    --admin-user="$(grep NEXTCLOUD_ADMIN_USER ../.env | cut -d '=' -f2)" \
    --admin-pass="$(grep NEXTCLOUD_ADMIN_PASSWORD ../.env | cut -d '=' -f2)" \
    --data-dir="/var/www/html/data" || true

# Configure trusted domains
print_status "Configuring trusted domains..."
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 0 --value="files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 1 --value="localhost"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 2 --value="nextcloud-web"

# Configure overwrite settings
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwrite.cli.url --value="https://files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwritehost --value="files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwriteprotocol --value="https"

# Configure Redis
print_status "Configuring Redis cache..."
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis host --value="nextcloud-redis"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis port --value="6379" --type=integer
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis password --value="$(grep REDIS_PASSWORD ../.env | cut -d '=' -f2)"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.local --value="\\OC\\Memcache\\APCu"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.distributed --value="\\OC\\Memcache\\Redis"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.locking --value="\\OC\\Memcache\\Redis"

# Configure default phone region
print_status "Setting default phone region..."
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set default_phone_region --value="$(grep DEFAULT_PHONE_REGION ../.env | cut -d '=' -f2)"

# Configure file handling
print_status "Configuring file handling..."
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set enable_previews --value=true --type=boolean
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set preview_max_x --value="2048" --type=integer
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set preview_max_y --value="2048" --type=integer
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set jpeg_quality --value="85" --type=integer

# Configure maintenance window
print_status "Setting maintenance window..."
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set maintenance_window_start --value=2 --type=integer

# Step 6: Install and configure apps
print_status "Installing essential apps..."

# Install Collabora Online connector
docker-compose exec -T -u www-data nextcloud-app php occ app:install richdocuments || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable richdocuments || true
docker-compose exec -T -u www-data nextcloud-app php occ config:app:set richdocuments wopi_url --value="https://office.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:app:set richdocuments public_wopi_url --value="https://office.acebuddy.quest"

# Install Talk (for notifications/websockets)
docker-compose exec -T -u www-data nextcloud-app php occ app:install spreed || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable spreed || true

# Install Notify Push
docker-compose exec -T -u www-data nextcloud-app php occ app:install notify_push || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable notify_push || true

# Now start the push service after notify_push is installed
print_status "Starting push notification service..."
# Uncomment the push service in docker-compose.yml
sed -i 's/# nextcloud-push:/nextcloud-push:/' docker-compose.yml
sed -i '/nextcloud-push:/,/ipv4_address: 172.20.0.54/s/^  # /  /' docker-compose.yml

# Uncomment push location in nginx config
sed -i '/# Push notifications/,/# }/s/^        # /        /' ../nginx/nginx.conf

# Start the push service
docker-compose up -d nextcloud-push nextcloud-web

# Configure notify_push
docker-compose exec -T -u www-data nextcloud-app php occ notify_push:setup https://files.acebuddy.quest/push || true

# Install Mail app
docker-compose exec -T -u www-data nextcloud-app php occ app:install mail || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable mail || true

# Install Calendar
docker-compose exec -T -u www-data nextcloud-app php occ app:install calendar || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable calendar || true

# Install Contacts
docker-compose exec -T -u www-data nextcloud-app php occ app:install contacts || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable contacts || true

# Install Deck (Kanban boards)
docker-compose exec -T -u www-data nextcloud-app php occ app:install deck || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable deck || true

# Install Notes
docker-compose exec -T -u www-data nextcloud-app php occ app:install notes || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable notes || true

# Install Tables
docker-compose exec -T -u www-data nextcloud-app php occ app:install tables || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable tables || true

# Step 7: Add missing indices
print_status "Adding missing database indices..."
docker-compose exec -T -u www-data nextcloud-app php occ db:add-missing-indices || true

# Step 8: Run maintenance repairs
print_status "Running maintenance repairs..."
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:repair --include-expensive || true

# Step 9: Configure background jobs
print_status "Configuring background jobs..."
docker-compose exec -T -u www-data nextcloud-app php occ background:cron

# Step 10: Configure email settings
print_status "Configuring email settings..."
if grep -q "your-email@acebuddy.quest" ../.env; then
    print_warning "Please update email settings in ../.env and re-run this script"
else
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpmode --value="smtp"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtphost --value="$(grep SMTP_HOST ../.env | cut -d '=' -f2)"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpport --value="$(grep SMTP_PORT ../.env | cut -d '=' -f2)" --type=integer
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpsecure --value="$(grep SMTP_SECURE ../.env | cut -d '=' -f2)"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpauth --value=true --type=boolean
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpname --value="$(grep SMTP_USERNAME ../.env | cut -d '=' -f2)"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtppassword --value="$(grep SMTP_PASSWORD ../.env | cut -d '=' -f2)"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_from_address --value="$(grep MAIL_FROM_ADDRESS ../.env | cut -d '=' -f2)"
    docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_domain --value="$(grep MAIL_DOMAIN ../.env | cut -d '=' -f2)"
fi

# Final status check
print_status "Running final status check..."
docker-compose exec -T -u www-data nextcloud-app php occ status

# Check if push service is running
if docker-compose ps | grep -q "nextcloud-push.*Up"; then
    print_status "Push notification service is running"
else
    print_warning "Push notification service failed to start - check logs with: docker-compose logs nextcloud-push"
fi

# Print access information
echo ""
print_status "✨ Nextcloud installation complete!"
echo ""
echo "Access URLs:"
echo "- Public: https://files.acebuddy.quest"
echo "- Local: http://localhost:8055"
echo ""
echo "Admin credentials:"
echo "- Username: $(grep NEXTCLOUD_ADMIN_USER ../.env | cut -d '=' -f2)"
echo "- Password: $(grep NEXTCLOUD_ADMIN_PASSWORD ../.env | cut -d '=' -f2)"
echo ""
echo "Collabora Office: https://office.acebuddy.quest"
echo ""
print_warning "Remember to:"
echo "1. Update email settings in ../.env if not done already"
echo "2. Check https://files.acebuddy.quest/settings/admin/overview for any remaining warnings"
echo ""
