# 🔐 Centralized Secrets Management for Matrix + MAS (2025 Edition)

## 📖 Overview

This setup implements modern best practices for managing secrets in your Matrix homeserver with MAS (Matrix Authentication Service) using centralized environment variables.

## 🏗️ Architecture

```
homelab/
├── .env                    # 🔐 Central secrets file (DO NOT COMMIT)
├── .env.example           # 📝 Example template 
├── deploy.sh              # 🚀 Master deployment script
├── mas/
│   ├── config.template.yaml    # 📄 MAS config template
│   ├── config.yaml            # 🔧 Generated config (DO NOT COMMIT)
│   ├── generate-config.sh     # 🛠️ Config generation script
│   └── docker-compose.yml     # 🐳 Updated with env vars
└── matrix/
    ├── update-synapse-config.sh # 🛠️ Synapse config updater
    └── docker-compose.yml      # 🐳 Updated with env vars
```

## 🚀 Quick Start

1. **Copy example environment file:**
   ```bash
   cd ~/homelab
   cp .env.example .env
   ```

2. **Edit .env with your actual values:**
   ```bash
   nano .env
   ```

3. **Deploy everything:**
   ```bash
   ./deploy.sh
   ```

## 🔑 Secret Generation

Generate your secrets using these commands:

```bash
# MAS Encryption Key (32 bytes)
openssl rand -hex 32

# Matrix Secret (48 bytes) 
openssl rand -hex 48

# Synapse Client Secret (48 bytes)
openssl rand -hex 48

# Database passwords (24 characters)
openssl rand -base64 24
```

## 🔧 Manual Operations

### Generate MAS Config Only
```bash
cd mas
./generate-config.sh
```

### Update Synapse Config Only  
```bash
cd matrix
./update-synapse-config.sh
```

### Restart Services
```bash
# Restart MAS
cd mas && docker-compose restart

# Restart Matrix 
cd matrix && docker-compose restart matrix-synapse
```

## 🏥 Health Checks

```bash
# Check MAS health
curl http://localhost:8081/health

# Validate MAS config
docker exec matrix-auth-service mas-cli config check

# Check service logs
docker logs -f matrix-auth-service
docker logs -f matrix-synapse
```

## 🛡️ Security Features

- ✅ Centralized secret management
- ✅ Environment variable substitution  
- ✅ No secrets in git repository
- ✅ Secure file permissions (600)
- ✅ Backup and rollback capability
- ✅ Config validation scripts

## 🔄 Secret Rotation

To rotate secrets:

1. Generate new secrets
2. Update .env file  
3. Run: `./deploy.sh`
4. Verify services are healthy

## 📝 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOMAIN` | Your primary domain | `example.com` |
| `MATRIX_DOMAIN` | Matrix server domain | `example.com` |
| `MAS_ENCRYPTION_KEY` | MAS encryption key (32 bytes hex) | `abc123...` |
| `MATRIX_SECRET` | Shared secret (48 bytes hex) | `def456...` | 
| `SYNAPSE_CLIENT_SECRET` | OIDC client secret (48 bytes hex) | `ghi789...` |
| `MAS_POSTGRES_PASSWORD` | MAS database password | `securepass123` |

## 🐛 Troubleshooting

### MAS Config Issues
```bash
# Validate template
cd mas && ./generate-config.sh

# Check logs
docker logs matrix-auth-service
```

### Synapse Issues  
```bash
# Update config
cd matrix && ./update-synapse-config.sh

# Check logs
docker logs matrix-synapse
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R $USER:$USER homelab/
chmod 600 homelab/.env
```

## 📚 References

- [Matrix Authentication Service Documentation](https://element-hq.github.io/matrix-authentication-service/)
- [MSC3861: Next-generation auth for Matrix](https://github.com/matrix-org/matrix-spec-proposals/pull/3861)
- [Element MAS Migration Guide](https://willlewis.co.uk/blog/posts/stronger-matrix-auth-mas-synapse-docker-compose/)

---
Last updated: $(date +"%Y-%m-%d")
