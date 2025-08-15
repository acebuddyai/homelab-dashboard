# 🏠 Homelab Dashboard & Services

## 📖 Overview

A comprehensive self-hosted homelab setup with an AI-powered dashboard, Matrix chat server, and integrated services for productivity and communication.

## 🖥️ Hardware Specifications

- **System**: HP EliteDesk 800 G4 DM
- **CPU**: Intel Core i5-8500T
- **RAM**: 32GB DDR4
- **Storage**: 512GB SSD
- **GPU**: None (CPU-only operation)

## 🚀 Features

### ✅ Implemented
- **AI Chat Interface**: Powered by Ollama with llama3.2:1b model
- **Matrix Homeserver**: Synapse with MAS authentication
- **Web Dashboard**: Modern UI with sidebar navigation
- **API Gateway**: Centralized service routing

### 🔄 In Progress
- **Email Server**: Local email hosting (Mailcow/Postfix)
- **Calendar**: CalDAV/CardDAV server (Radicale)
- **Cloud Storage**: Nextcloud integration
- **Knowledge Base**: Document management system
- **Task Management**: Todo lists and project tracking

## 🏗️ Architecture

```
homelab/
├── .env                    # 🔐 Central secrets file (DO NOT COMMIT)
├── .env.example           # 📝 Example template 
├── docker-compose.yml     # 🐳 Main services
├── web-ui/                # 🎨 Dashboard interface
│   ├── index.html         # Main dashboard
│   ├── dashboard.html     # Full dashboard view
│   └── app.js            # Backend API server
├── matrix/               # 💬 Matrix chat server
│   └── docker-compose.yml
├── mas/                  # 🔑 Matrix Authentication Service
│   └── docker-compose.yml
├── nextcloud/            # ☁️ Cloud storage (coming soon)
├── services/             # 📦 Additional services
└── scripts/              # 🛠️ Utility scripts
```

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/homelab.git
   cd homelab
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Deploy all services:**
   ```bash
   ./deploy.sh
   ```

4. **Access the dashboard:**
   ```
   http://localhost:8080
   ```

## 🎯 Dashboard Features

### AI Chat
- Ollama integration with CPU-optimized models
- Real-time conversation interface
- Response time: 1-3 seconds
- Memory usage: 8-12GB allocated

### Daily Briefing
- Weather updates
- Calendar events
- News aggregation
- Task reminders

### Services Integration
- **Email**: Local email server with webmail interface
- **Calendar**: CalDAV/CardDAV support for all devices
- **Drive**: Nextcloud for file storage and sync
- **Tasks**: Project and task management
- **Knowledge Base**: Documentation and notes

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Dashboard | 8080 | Main web interface |
| Ollama | 11434 | AI model server |
| Matrix | 8008 | Chat server |
| MAS | 8081 | Authentication service |
| Nextcloud | 8082 | Cloud storage (planned) |
| Email | 8083 | Webmail interface (planned) |
| Calendar | 8084 | CalDAV server (planned) |

## 🔑 Secret Management

### Generate secrets:
```bash
# MAS Encryption Key (32 bytes)
openssl rand -hex 32

# Matrix Secret (48 bytes) 
openssl rand -hex 48

# Database passwords (24 characters)
openssl rand -base64 24
```

### Environment Variables:
| Variable | Description |
|----------|-------------|
| `DOMAIN` | Your primary domain |
| `MATRIX_DOMAIN` | Matrix server domain |
| `MAS_ENCRYPTION_KEY` | MAS encryption key |
| `MATRIX_SECRET` | Shared secret |
| `MAS_POSTGRES_PASSWORD` | MAS database password |

## 🛠️ Maintenance

### Update services:
```bash
docker-compose pull
docker-compose up -d
```

### Check logs:
```bash
docker logs -f [service-name]
```

### Backup data:
```bash
./scripts/backup.sh
```

## 🏥 Health Checks

```bash
# Check all services
docker-compose ps

# AI Chat health
curl http://localhost:11434/api/tags

# Matrix health
curl http://localhost:8008/_matrix/client/versions

# Dashboard health
curl http://localhost:8080
```

## 🐛 Troubleshooting

### AI Chat Issues
- Ensure Ollama is running: `docker ps | grep ollama`
- Check memory allocation: `docker stats ollama`
- Pull model if missing: `docker exec ollama ollama pull llama3.2:1b`

### Dashboard Issues
- Clear browser cache: Ctrl+Shift+R
- Check console logs: F12 → Console
- Restart service: `docker-compose restart web-ui`

## 📝 Planned Features

- [ ] Email server with IMAP/SMTP
- [ ] Calendar with CalDAV sync
- [ ] Nextcloud integration
- [ ] Automated backups
- [ ] Monitoring dashboard
- [ ] VPN server
- [ ] Media server (Jellyfin)
- [ ] Home automation (Home Assistant)

## 🔒 Security Features

- ✅ Centralized secret management
- ✅ Environment variable substitution  
- ✅ No secrets in git repository
- ✅ Secure file permissions (600)
- ✅ Docker network isolation
- ✅ Reverse proxy with Caddy

## 📚 Documentation

- [Matrix Authentication Service](https://element-hq.github.io/matrix-authentication-service/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Nextcloud Admin Manual](https://docs.nextcloud.com/server/latest/admin_manual/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---
**System Optimized for**: HP EliteDesk 800 G4 DM with 32GB RAM  
**Last Updated**: January 2025