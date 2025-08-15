#!/bin/bash
set -e

echo "Configuring Nextcloud..."

# Configure trusted domains
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 0 --value="files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 1 --value="localhost"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set trusted_domains 2 --value="nextcloud-web"

# Configure overwrite settings
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwrite.cli.url --value="https://files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwritehost --value="files.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set overwriteprotocol --value="https"

# Configure Redis
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis host --value="nextcloud-redis"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis port --value="6379" --type=integer
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set redis password --value="redis_secure_pass_2024"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.local --value="\\OC\\Memcache\\APCu"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.distributed --value="\\OC\\Memcache\\Redis"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set memcache.locking --value="\\OC\\Memcache\\Redis"

# Configure default phone region
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set default_phone_region --value="US"

# Configure maintenance window
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set maintenance_window_start --value=2 --type=integer

# Configure background jobs
docker-compose exec -T -u www-data nextcloud-app php occ background:cron

# Add missing indices
docker-compose exec -T -u www-data nextcloud-app php occ db:add-missing-indices

# Run maintenance repairs
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:repair --include-expensive

echo "Configuration complete!"
