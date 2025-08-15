# Node-RED Configuration for Homelab AI Assistant

## Overview

Node-RED is a flow-based development tool for visual programming, perfect for wiring together devices, APIs, and online services. In our homelab setup, it replaces Windmill for workflow automation and provides a more intuitive interface for creating automations.

## Features

- **Visual Programming**: Drag-and-drop interface for creating flows
- **Extensive Node Library**: Thousands of community-contributed nodes
- **Home Assistant Integration**: Easy integration with home automation
- **API Integration**: Connect to any REST API or webhook
- **Real-time Debugging**: Built-in debug capabilities
- **Dashboard Creation**: Build custom dashboards with UI nodes

## Default Configuration

- **Port**: 1880
- **URL**: http://localhost:1880 or https://workflows.acebuddy.quest
- **Data Directory**: /data (in container)
- **User**: Runs as UID 1000 (non-root)

## Security Setup

### 1. Generate Admin Password

First, generate a password hash for the admin user:

```bash
# Connect to the Node-RED container
docker exec -it node-red bash

# Generate password hash
node -e "console.log(require('bcryptjs').hashSync('your-password-here', 8));"
```

### 2. Enable Authentication

Edit `settings.js` and uncomment the `adminAuth` section:

```javascript
adminAuth: {
    type: "credentials",
    users: [{
        username: "admin",
        password: "$2b$08$YOUR_HASH_HERE",
        permissions: "*"
    }],
    default: {
        permissions: "read"
    }
},
```

### 3. Set Credential Secret

Add to your `.env` file:

```bash
NODE_RED_CREDENTIAL_SECRET=your-super-secret-key-here
```

This encrypts stored credentials in flows.

## Installing Additional Nodes

### Via Web Interface

1. Open Node-RED at http://localhost:1880
2. Click the hamburger menu → Manage palette
3. Go to the "Install" tab
4. Search for nodes and click install

### Popular Nodes for Homelab

```bash
# Home Assistant
node-red-contrib-home-assistant-websocket

# Dashboard
node-red-dashboard

# Email
node-red-node-email

# Telegram
node-red-contrib-telegrambot

# HTTP Request enhancements
node-red-contrib-http-request

# Cron scheduling
node-red-contrib-cron-plus

# File operations
node-red-contrib-fs-ops

# Docker management
node-red-contrib-dockerode

# Database
node-red-node-mysql
node-red-contrib-postgresql
node-red-contrib-mongodb

# MQTT
node-red-contrib-mqtt-broker
```

## Example Flows

### 1. Daily System Health Check

```json
[
    {
        "id": "daily-health-check",
        "type": "inject",
        "cron": "0 9 * * *",
        "topic": "health-check"
    },
    {
        "id": "check-services",
        "type": "http request",
        "method": "GET",
        "url": "http://localhost:3000/health"
    },
    {
        "id": "send-notification",
        "type": "email",
        "to": "admin@example.com",
        "subject": "Daily Health Report"
    }
]
```

### 2. AI Chat Integration

Connect Node-RED to the Ollama service:

```javascript
// Function node to query Ollama
msg.payload = {
    model: "llama3.2:latest",
    messages: [
        { role: "user", content: msg.payload }
    ]
};
msg.headers = {
    "Content-Type": "application/json"
};
msg.url = "http://ollama:11434/api/chat";
return msg;
```

### 3. Backup Automation

Create automated backups of Node-RED flows:

```javascript
// Function node for backup
const date = new Date().toISOString().split('T')[0];
msg.filename = `/data/backup/flows_${date}.json`;
msg.payload = flow.get('flows') || [];
return msg;
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_RED_CREDENTIAL_SECRET` | Secret for encrypting credentials | (none) |
| `NODE_RED_ENABLE_PROJECTS` | Enable Git projects feature | false |
| `NODE_RED_ENABLE_SAFE_MODE` | Start in safe mode (no flows) | false |
| `TZ` | Timezone | America/New_York |

## Backup and Restore

### Backup Flows

```bash
# Backup current flows
docker exec node-red cat /data/flows.json > flows_backup.json

# Backup with timestamp
docker exec node-red cat /data/flows.json > flows_$(date +%Y%m%d_%H%M%S).json

# Backup credentials (encrypted)
docker exec node-red cat /data/flows_cred.json > flows_cred_backup.json

# Full backup including node_modules
docker cp node-red:/data ./node-red-backup-$(date +%Y%m%d)
```

### Restore Flows

```bash
# Restore flows
docker cp flows_backup.json node-red:/data/flows.json

# Restore credentials
docker cp flows_cred_backup.json node-red:/data/flows_cred.json

# Restart Node-RED to apply
docker restart node-red
```

## Integration with Homelab Services

### Ollama (AI/LLM)

- Endpoint: `http://ollama:11434`
- Use HTTP Request node to query models
- Parse streaming responses with function nodes

### Qdrant (Vector Database)

- Endpoint: `http://qdrant:6333`
- Store and search embeddings
- Use for semantic search in flows

### Redis (Cache)

- Host: `ai-redis`
- Port: `6379`
- Use node-red-contrib-redis for caching

### API Gateway

- Endpoint: `http://api-gateway:3000`
- Central API access point
- Authenticated requests to services

## Troubleshooting

### Permission Issues

If you see permission errors:

```bash
# Fix permissions on host
sudo chown -R 1000:1000 /path/to/node-red/data

# Or in docker-compose.yml, remove user directive
# user: "1000:1000"  # Comment this out
```

### Cannot Install Nodes

If palette manager fails:

```bash
# Install directly via npm
docker exec -it node-red npm install node-red-dashboard

# Restart Node-RED
docker restart node-red
```

### Flows Not Saving

Check disk space and permissions:

```bash
# Check disk space
docker exec node-red df -h /data

# Check write permissions
docker exec node-red touch /data/test.txt
```

### High Memory Usage

Limit memory in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
```

## Best Practices

1. **Version Control**: Export and commit flows regularly
2. **Modular Flows**: Break complex automations into subflows
3. **Error Handling**: Always add catch nodes for error handling
4. **Documentation**: Use comment nodes to document flows
5. **Security**: Never hardcode credentials, use environment variables
6. **Testing**: Test flows in debug mode before deploying
7. **Backup**: Automate flow backups daily

## Useful Resources

- [Node-RED Documentation](https://nodered.org/docs/)
- [Node-RED Cookbook](https://cookbook.nodered.org/)
- [Flow Library](https://flows.nodered.org/)
- [Node-RED Forum](https://discourse.nodered.org/)
- [Node-RED on Docker](https://nodered.org/docs/getting-started/docker)

## Migration from Windmill

If you're migrating from Windmill:

1. Export any Windmill workflows as JSON/YAML
2. Recreate logic in Node-RED using appropriate nodes
3. Test thoroughly in Node-RED debug mode
4. Update any API endpoints that referenced Windmill

## Support

For issues specific to this homelab setup:
- Check the main [DEPLOYMENT.md](../DEPLOYMENT.md)
- Review container logs: `docker logs node-red`
- Access Node-RED logs in UI: Deploy → Debug tab