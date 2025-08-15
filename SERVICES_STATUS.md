# 🚀 Homelab Services Status

## ✅ Current Deployment Status: OPERATIONAL

### Last Updated: August 15, 2025
### System: HP EliteDesk 800 G4 DM | 32GB RAM | Intel Core i5-8500T

---

## 🌐 Public Services (acebuddy.quest)

All services are accessible via HTTPS with valid SSL certificates through Caddy reverse proxy.

| Service | URL | Status | Description |
|---------|-----|--------|-------------|
| **AI Dashboard** | https://ai.acebuddy.quest | ✅ ONLINE | Main dashboard with AI chat, sidebar navigation |
| **Webmail** | https://mail.acebuddy.quest | ✅ ONLINE | Roundcube webmail interface |
| **Calendar** | https://calendar.acebuddy.quest | ✅ ONLINE | Baikal CalDAV/CardDAV server |
| **Cloud Storage** | https://files.acebuddy.quest | ✅ ONLINE | Nextcloud file storage and sync |
| **AI Chat** | https://chat.acebuddy.quest | ✅ ONLINE | Open WebUI for Ollama models |
| **Workflows** | https://workflows.acebuddy.quest | ✅ ONLINE | Windmill automation platform |
| **Tasks** | https://tasks.acebuddy.quest | ✅ ONLINE | Vikunja task management |
| **Search** | https://search.acebuddy.quest | ✅ ONLINE | SearXNG privacy search |
| **Status Page** | https://status.acebuddy.quest | ✅ ONLINE | Service monitoring dashboard |
| **API Gateway** | https://api.acebuddy.quest | ✅ ONLINE | RESTful API endpoint |
| **Vector DB** | https://vectors.acebuddy.quest | ✅ ONLINE | Qdrant vector database |

---

## 🖥️ Local Services

| Service | Port | Status | Access URL |
|---------|------|--------|------------|
| Dashboard | 8080 | ✅ Running | http://localhost:8080 |
| Ollama API | 11434 | ✅ Running | http://localhost:11434 |
| Roundcube | 8086 | ✅ Running | http://localhost:8086 |
| Baikal | 5233 | ✅ Running | http://localhost:5233 |
| API Gateway | 3000 | ✅ Running | http://localhost:3000 |
| Windmill | 8000 | ✅ Running | http://localhost:8000 |
| Caddy | 80/443 | ✅ Running | Reverse proxy |

---

## 🐳 Docker Containers

### Core Services
- ✅ `web-ui` - Dashboard interface (healthy)
- ✅ `ollama` - AI model server (running)
- ✅ `api-gateway` - Service routing (running)
- ✅ `caddy` - Reverse proxy (running)

### Communication & Collaboration
- ✅ `roundcube` - Webmail client (running)
- ✅ `baikal` - CalDAV/CardDAV server (running)
- ✅ `nextcloud` - Cloud storage (running)
- ✅ `nextcloud-db` - PostgreSQL for Nextcloud (running)

### Automation & Productivity
- ✅ `windmill-server` - Workflow server (running)
- ✅ `windmill-worker` - Workflow executor (running)
- ✅ `windmill-db` - PostgreSQL for Windmill (healthy)
- ✅ `vikunja` - Task management (running)
- ✅ `open-webui` - Chat interface (healthy)

### Search & Analytics
- ✅ `searxng` - Search engine (running)
- ✅ `qdrant` - Vector database (running)
- ✅ `homelab-status` - Status monitoring (healthy)

### Support Services
- ✅ `ai-redis` - Redis cache (healthy)

---

## 🎯 Dashboard Features

The main dashboard at https://ai.acebuddy.quest includes:

### Integrated Features (Built-in)
- **AI Chat** - Direct chat with llama3.2:1b model
- **Daily Briefing** - AI-generated summaries
- **Tasks** - Task management interface
- **Knowledge Base** - Document storage
- **Workflows** - Automation tools
- **Web Search** - Integrated search
- **Analytics** - Usage statistics

### External Services (Sidebar Links)
- **Email** - Opens Roundcube webmail
- **Calendar** - Opens Baikal interface
- **Nextcloud** - Opens cloud storage
- **Open WebUI** - Advanced AI chat
- **Windmill** - Workflow automation
- **Vikunja** - Advanced task management
- **Status Page** - Service monitoring

---

## 📧 Email Configuration

### Server Details
- **Type**: Roundcube webmail (frontend only)
- **Access**: https://mail.acebuddy.quest
- **Backend**: Requires external IMAP/SMTP server
- **Status**: Interface operational, needs mail server configuration

### To Complete Email Setup
1. Configure external IMAP server in Roundcube
2. Or deploy full mail server (Maddy/Postfix)
3. Create user accounts
4. Configure DNS records (MX, SPF, DKIM)

---

## 📅 Calendar Configuration

### Server Details
- **Type**: Baikal CalDAV/CardDAV
- **Access**: https://calendar.acebuddy.quest
- **Admin**: https://calendar.acebuddy.quest/admin/
- **Protocol**: CalDAV (calendars), CardDAV (contacts)

### Client Configuration
- **Server**: calendar.acebuddy.quest
- **Port**: 443 (HTTPS)
- **Path**: /dav.php/calendars/[username]/
- **Authentication**: Basic auth

### Tested Clients
- Thunderbird (with TbSync)
- iOS Calendar/Contacts
- Android (DAVx⁵)
- Evolution

---

## ☁️ Cloud Storage (Nextcloud)

### Access Details
- **URL**: https://files.acebuddy.quest
- **Status**: Login page active
- **Admin Setup**: Required on first login
- **Features**: File sync, sharing, collaboration

### Default Credentials
- Create admin account on first login
- Or use environment variables for auto-setup

---

## 🤖 AI Services

### Ollama Configuration
- **Model**: llama3.2:1b (CPU-optimized)
- **Memory**: 8-12GB allocated
- **API**: http://localhost:11434
- **Response Time**: 1-3 seconds

### Open WebUI
- **URL**: https://chat.acebuddy.quest
- **Backend**: Ollama
- **Features**: Advanced chat, model management

---

## 🔧 Management Commands

### Check All Services
```bash
./check-services.sh
```

### View Logs
```bash
# All services
docker-compose -f docker-compose-ai-stack.yml logs -f

# Specific service
docker logs -f [container-name]
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose-ai-stack.yml restart

# Specific service
docker restart [container-name]
```

### Deploy New Services
```bash
./deploy-integrated.sh
```

---

## 🛠️ Known Issues & TODOs

### Issues
- ❌ Maddy mail server - Config file issues, needs fix
- ⚠️ API Gateway - Shows unhealthy but functioning
- ⚠️ Email - Frontend only, needs backend mail server

### TODO
- [ ] Configure full email server (SMTP/IMAP)
- [ ] Set up Nextcloud admin account
- [ ] Create calendar users
- [ ] Configure automated backups
- [ ] Add monitoring with Prometheus/Grafana
- [ ] Set up VPN for secure remote access
- [ ] Configure firewall rules
- [ ] Document router port forwarding

---

## 📊 Resource Usage

### Current Usage
- **Containers**: 16 running
- **Memory**: ~12-15GB used of 32GB
- **CPU**: Low usage (5-10%)
- **Disk**: Check with `df -h`

### Service Memory
- Ollama: 8-12GB
- Nextcloud + DB: 2-4GB
- Windmill: 1-2GB
- Others: <500MB each

---

## 🔒 Security Status

### Current Configuration
- ✅ HTTPS with Caddy automatic SSL
- ✅ Services isolated in Docker networks
- ✅ No direct port exposure (via Caddy proxy)
- ⚠️ Firewall inactive (UFW not enabled)
- ⚠️ Some services without authentication

### Recommendations
1. Enable UFW firewall
2. Configure authentication for all services
3. Set up fail2ban
4. Regular security updates
5. Implement backup strategy

---

## 📚 Quick Links

### Documentation
- **GitHub**: https://github.com/acebuddyai/homelab-dashboard
- **Deployment Guide**: See DEPLOYMENT_SUMMARY.md
- **User Management**: See manage-users.sh scripts

### Support
- **Ollama Docs**: https://ollama.ai/docs
- **Nextcloud Admin**: https://docs.nextcloud.com
- **Baikal Wiki**: https://sabre.io/baikal/
- **Caddy Docs**: https://caddyserver.com/docs/

---

**Status**: ✅ All critical services operational  
**Last Check**: August 15, 2025  
**Next Steps**: Configure email backend, set up user accounts, enable firewall