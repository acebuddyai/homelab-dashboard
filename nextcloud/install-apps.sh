#!/bin/bash
set -e

echo "Installing Nextcloud apps..."

# Install Collabora Online connector
echo "Installing Collabora connector..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install richdocuments || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable richdocuments || true
docker-compose exec -T -u www-data nextcloud-app php occ config:app:set richdocuments wopi_url --value="https://office.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:app:set richdocuments public_wopi_url --value="https://office.acebuddy.quest"

# Install Talk for high-performance backend
echo "Installing Talk..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install spreed || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable spreed || true

# Install Mail app
echo "Installing Mail..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install mail || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable mail || true

# Install Calendar
echo "Installing Calendar..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install calendar || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable calendar || true

# Install Contacts
echo "Installing Contacts..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install contacts || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable contacts || true

# Install Deck (Kanban boards)
echo "Installing Deck..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install deck || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable deck || true

# Install Notes
echo "Installing Notes..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install notes || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable notes || true

# Install Tables
echo "Installing Tables..."
docker-compose exec -T -u www-data nextcloud-app php occ app:install tables || true
docker-compose exec -T -u www-data nextcloud-app php occ app:enable tables || true

echo "Apps installation complete!"
