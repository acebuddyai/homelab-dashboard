# Nextcloud Hub - Complete Installation

## 🚀 Overview

This is a comprehensive Nextcloud Hub installation with Redis caching, PostgreSQL database, Collabora Online office suite, and nginx web server. The setup includes performance optimizations and all essential productivity apps.

## 📦 Services Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Caddy Reverse Proxy                │
│                 (files.acebuddy.quest)               │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│                  Nginx Web Server                    │
│                  (nextcloud-web)                     │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Nextcloud FPM Application               │
│                 (nextcloud-app)                      │
└──┬──────────────┬──────────────┬────────────────────┘
   │              │              │
┌──▼───┐    ┌────▼────┐    ┌────▼────┐
│Redis │    │PostgreSQL│    │Collabora│
│Cache │    │Database  │    │ Office  │
└──────┘    └──────────┘    └─────────┘
```

### Container Services

| Service | Container Name | IP Address | Purpose |
|---------|---------------|------------|---------|
| Database | nextcloud-db | 172.20.0.50 | PostgreSQL 16 database |
| Cache | nextcloud-redis | 172.20.0.58 | Redis cache for performance |
| Office | nextcloud-collabora | 172.20.0.53 | Collabora Online document editing |
| App Server | nextcloud-app | 172.20.0.51 | PHP-FPM application server |
| Web Server | nextcloud-web | 172.20.0.55 | Nginx web server |
| Cron | nextcloud-cron | 172.20.0.56 | Background job processor |

## 🔑 Access Information

### Public URLs
- **Main Interface**: https://files.acebuddy.quest
- **Office Suite**: https://office.acebuddy.quest

### Admin Credentials
- **Username**: admin
- **Password**: admin_secure_pass_2024

> ⚠️ **Important**: Change the admin password after first login!

## ✨ Installed Features

### Core Apps
- **📧 Mail** - Full email client integration
- **📅 Calendar** - CalDAV calendar with event management
- **👥 Contacts** - CardDAV contact management
- **💬 Talk** - Video calls and chat (requires high-performance backend)
- **📝 Notes** - Markdown note-taking
- **📋 Deck** - Kanban board for project management
- **📊 Tables** - Spreadsheet functionality
- **📄 Collabora Online** - Full office suite (Word, Excel, PowerPoint equivalents)

### Performance Optimizations
- ✅ Redis caching (local, distributed, and locking)
- ✅ PostgreSQL 16 database
- ✅ PHP OPcache configured with 256MB
- ✅ 2GB PHP memory limit
- ✅ 10GB file upload limit
- ✅ Nginx web server with optimized configuration
- ✅ Background job processing via cron

## 🛠️ Configuration Details

### Environment Variables
Environment variables are stored in `/home/relock/homelab/.env`:
```bash
NEXTCLOUD_DB_PASSWORD=nc_db_secure_pass_2024
REDIS_PASSWORD=redis_secure_pass_2024
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=admin_secure_pass_2024
COLLABORA_USERNAME=admin
COLLABORA_PASSWORD=collabora_secure_pass_2024
DEFAULT_PHONE_REGION=US
```

### PHP Configuration
Custom PHP settings in `config/php.ini`:
- Memory limit: 2GB
- Upload max filesize: 10GB
- OPcache: 256MB
- Session handler: Redis

### Security Headers
All security headers are properly configured:
- ✅ Strict-Transport-Security (HSTS)
- ✅ X-Content-Type-Options
- ✅ X-Frame-Options
- ✅ X-XSS-Protection
- ✅ Referrer-Policy
- ✅ Content-Security-Policy

## 📝 Common Tasks

### Check System Status
```bash
cd /home/relock/homelab/nextcloud
docker-compose exec -T -u www-data nextcloud-app php occ status
```

### Add Missing Database Indices
```bash
docker-compose exec -T -u www-data nextcloud-app php occ db:add-missing-indices
```

### Run Maintenance Repairs
```bash
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:repair --include-expensive
```

### Install Additional Apps
```bash
# List available apps
docker-compose exec -T -u www-data nextcloud-app php occ app:list

# Install an app
docker-compose exec -T -u www-data nextcloud-app php occ app:install <app_name>

# Enable an app
docker-compose exec -T -u www-data nextcloud-app php occ app:enable <app_name>
```

### Configure Email Settings
```bash
# Set SMTP configuration
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpmode --value="smtp"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtphost --value="mail.acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpport --value="587" --type=integer
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpsecure --value="tls"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpauth --value=true --type=boolean
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtpname --value="your-email@acebuddy.quest"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_smtppassword --value="your-password"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_from_address --value="nextcloud"
docker-compose exec -T -u www-data nextcloud-app php occ config:system:set mail_domain --value="acebuddy.quest"
```

## 🔧 Maintenance

### Start/Stop Services
```bash
cd /home/relock/homelab/nextcloud

# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart nextcloud-app
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f nextcloud-app
docker-compose logs -f nextcloud-web
```

### Backup Database
```bash
# Create backup
docker-compose exec nextcloud-db pg_dump -U nextcloud nextcloud > backup.sql

# Restore backup
docker-compose exec -T nextcloud-db psql -U nextcloud nextcloud < backup.sql
```

### Update Nextcloud
```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d

# Run post-update tasks
docker-compose exec -T -u www-data nextcloud-app php occ upgrade
docker-compose exec -T -u www-data nextcloud-app php occ db:add-missing-indices
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:repair
```

## 🚨 Troubleshooting

### Check Service Health
```bash
docker-compose ps
docker-compose exec nextcloud-app php -v
docker-compose exec nextcloud-db pg_isready -U nextcloud
docker-compose exec nextcloud-redis redis-cli ping
```

### Common Issues

#### 502 Bad Gateway
- Check if all services are running: `docker-compose ps`
- Check nginx logs: `docker-compose logs nextcloud-web`
- Verify app server is healthy: `docker-compose logs nextcloud-app`

#### Slow Performance
- Check Redis connection: `docker-compose exec -T -u www-data nextcloud-app php occ config:list system | grep redis`
- Verify OPcache is enabled: `docker-compose exec nextcloud-app php -i | grep opcache`
- Check database performance: `docker-compose exec nextcloud-db psql -U nextcloud -c "SELECT pg_stat_activity"`

#### File Upload Issues
- Check PHP limits: `docker-compose exec nextcloud-app php -i | grep -E "(upload_max_filesize|post_max_size|memory_limit)"`
- Verify nginx client_max_body_size in `nginx/nginx.conf`

#### Collabora Not Working
- Check Collabora status: `docker-compose logs collabora`
- Verify WOPI settings: `docker-compose exec -T -u www-data nextcloud-app php occ config:app:get richdocuments wopi_url`

### Reset Admin Password
```bash
docker-compose exec -T -u www-data nextcloud-app php occ user:resetpassword admin
```

### Enable/Disable Maintenance Mode
```bash
# Enable maintenance mode
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:mode --on

# Disable maintenance mode
docker-compose exec -T -u www-data nextcloud-app php occ maintenance:mode --off
```

## 📊 Performance Monitoring

### Check Cache Statistics
```bash
# Redis memory usage
docker-compose exec nextcloud-redis redis-cli INFO memory

# Redis hit rate
docker-compose exec nextcloud-redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
```

### Database Statistics
```bash
# Database size
docker-compose exec nextcloud-db psql -U nextcloud -c "SELECT pg_database_size('nextcloud')"

# Active connections
docker-compose exec nextcloud-db psql -U nextcloud -c "SELECT count(*) FROM pg_stat_activity"
```

## 🔐 Security Recommendations

1. **Change default passwords** immediately after installation
2. **Enable 2FA** for all admin accounts
3. **Configure fail2ban** for brute force protection
4. **Regular backups** of database and data directory
5. **Keep Nextcloud updated** to latest stable version
6. **Configure email** for password resets and notifications
7. **Review sharing settings** and disable public sharing if not needed
8. **Enable encryption** for sensitive data

## 📚 Additional Resources

- [Nextcloud Documentation](https://docs.nextcloud.com/)
- [Nextcloud Apps Store](https://apps.nextcloud.com/)
- [Collabora Online Documentation](https://www.collaboraoffice.com/code/)
- [Performance Tuning Guide](https://docs.nextcloud.com/server/latest/admin_manual/installation/server_tuning.html)
- [Security Hardening Guide](https://docs.nextcloud.com/server/latest/admin_manual/installation/harden_server.html)

## 🆘 Support

For issues specific to this installation:
1. Check the logs: `docker-compose logs -f`
2. Review this README for common solutions
3. Check Nextcloud admin panel: https://files.acebuddy.quest/settings/admin/overview

---

**Last Updated**: August 15, 2025  
**Nextcloud Version**: 31.0.7  
**Installation Type**: Docker Compose with FPM + Nginx