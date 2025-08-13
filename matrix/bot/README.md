# Matrix Bot for acebuddy.quest

A simple, extensible Matrix bot built with Python and matrix-nio that can join encrypted rooms and respond to commands.

## Features

- **Encryption Support**: Full E2E encryption support for secure rooms
- **Command-based interaction**: Responds to commands with configurable prefix (default: `!bot`)
- **Room management**: Automatically joins specified rooms
- **Persistent storage**: Maintains login state and encryption keys between restarts
- **Docker deployment**: Easy containerized deployment
- **Environment-based configuration**: Secure credential management
- **Logging**: Comprehensive logging for monitoring and debugging

## Available Commands

- `!bot help` - Show help message with all available commands
- `!bot ping` - Simple ping/pong response
- `!bot info` - Display bot and room information
- `!bot status` - Show bot health status
- `!bot echo <message>` - Echo back the provided message
- `!bot room` - Display current room information

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to Matrix homeserver
- Bot user account with appropriate permissions

### Setup

1. **Configure environment variables**:
   ```bash
   cd homelab/matrix/bot
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **Build and start the bot**:
   ```bash
   cd homelab/matrix
   docker-compose up -d matrix-bot
   ```

3. **Check bot status**:
   ```bash
   docker-compose logs matrix-bot
   ```

4. **View live logs**:
   ```bash
   docker-compose logs -f matrix-bot
   ```

## Configuration

The bot uses environment variables for all configuration, including sensitive credentials. You must create a `.env` file in the bot directory.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MATRIX_HOMESERVER_URL` | Matrix homeserver URL | `https://matrix.example.com` |
| `MATRIX_BOT_USERNAME` | Bot's Matrix username | `@mybot:example.com` |
| `MATRIX_BOT_PASSWORD` | Bot's Matrix password | `your-secure-password` |
| `MATRIX_TARGET_ROOM_ID` | Room to join on startup | `!roomid:example.com` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_COMMAND_PREFIX` | `!bot` | Command prefix for bot interactions |
| `BOT_GREETING_MESSAGE` | Default greeting | Message sent when joining a room |
| `MATRIX_SYNC_TIMEOUT` | `30000` | Matrix sync timeout in milliseconds |
| `BOT_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `BOT_STORE_DIR` | `/app/store` | Directory for persistent bot data |

### Setting Up Environment Variables

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file** with your actual values:
   ```bash
   # Matrix Server Configuration
   MATRIX_HOMESERVER_URL=https://matrix.acebuddy.quest
   MATRIX_BOT_USERNAME=@yourbot:acebuddy.quest
   MATRIX_BOT_PASSWORD=your-actual-password
   
   # Room Configuration
   MATRIX_TARGET_ROOM_ID=!your-room-id:acebuddy.quest
   ```

3. **Verify the file is ignored by git**:
   The `.env` file is automatically ignored and will not be committed to version control.

## Security

### Credential Management

- **Never commit `.env` files**: Credentials are kept out of version control
- **Environment isolation**: Each service uses its own environment configuration
- **Docker secrets**: Credentials are only available within the container
- **Non-root execution**: Bot runs as unprivileged user inside container

### Encryption Support

- **E2E Encryption**: Full support for encrypted Matrix rooms
- **Device Verification**: Automatic device trust for seamless operation
- **Key Persistence**: Encryption keys stored securely in Docker volumes
- **Historical Messages**: Cannot decrypt messages sent before bot joined

## Architecture

### File Structure

```
bot/
├── bot.py              # Main bot application (config-based)
├── enhanced_bot.py     # Enhanced bot with hardcoded encryption
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
├── .env               # Environment variables (not in git)
├── .env.example       # Environment template
└── README.md          # This file
```

### Components

1. **MatrixBot/EnhancedMatrixBot**: Main bot logic and event handling
2. **BotConfig Class**: Environment-based configuration management
3. **Encryption Handler**: E2E encryption support for secure rooms
4. **Command Processor**: User command handling and responses
5. **Docker Container**: Isolated runtime environment

### Dependencies

- `matrix-nio[e2e]` - Matrix client library with encryption support
- `aiofiles` - Async file operations
- Standard Python libraries for logging and configuration

## Development

### Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the bot**:
   ```bash
   python enhanced_bot.py  # For encryption support
   # OR
   python bot.py          # For basic functionality
   ```

### Adding New Commands

To add a new command, modify the command handling section:

```python
elif command == f"!bot mycommand":
    await self.send_message(room.room_id, "My custom response!")
```

### Environment Variables in Development

For local development, you can also set environment variables directly:

```bash
export MATRIX_HOMESERVER_URL="https://matrix.acebuddy.quest"
export MATRIX_BOT_USERNAME="@yourbot:acebuddy.quest"
export MATRIX_BOT_PASSWORD="your-password"
python enhanced_bot.py
```

## Deployment

### Docker Compose

The bot is deployed as part of the Matrix stack:

```yaml
matrix-bot:
  build: ./bot
  container_name: matrix-bot
  restart: unless-stopped
  env_file: ./bot/.env  # Environment variables loaded from file
  volumes:
    - matrix_bot_store:/app/store
```

### Management Commands

```bash
# View logs
docker-compose logs matrix-bot

# Restart bot
docker-compose restart matrix-bot

# Stop bot
docker-compose stop matrix-bot

# Rebuild and restart
docker-compose up -d --build matrix-bot
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables" error**:
   - Ensure `.env` file exists in `homelab/matrix/bot/`
   - Verify all required variables are set
   - Check for typos in variable names

2. **Bot not responding to commands**:
   - Check if bot successfully joined the room
   - Verify command prefix matches configuration
   - Check bot logs for encryption/decryption errors

3. **Login failures**:
   - Verify username and password in `.env` file
   - Check homeserver URL is accessible
   - Ensure Matrix server is running

4. **Encryption issues**:
   - Bot cannot decrypt historical messages (this is normal)
   - Check device verification status
   - Verify encryption store persistence

### Debugging

1. **Enable debug logging**:
   ```bash
   # In .env file:
   BOT_LOG_LEVEL=DEBUG
   ```

2. **Check detailed logs**:
   ```bash
   docker-compose logs --tail 100 matrix-bot
   ```

3. **Verify environment variables**:
   ```bash
   docker-compose exec matrix-bot env | grep MATRIX
   ```

## Monitoring

### Health Checks

Use the `!bot status` command to verify:
- Bot connectivity and login status
- Room membership
- Encryption status
- Connected room count

### Log Monitoring

Monitor for these log patterns:
- `✅` - Successful operations
- `❌` - Errors requiring attention
- `🔐` - Encryption-related events
- `🤖` - Command processing

## Migration from Hardcoded Configuration

If upgrading from a version with hardcoded credentials:

1. **Create `.env` file** from template
2. **Fill in your actual credentials**
3. **Restart the bot service**
4. **Verify operation** with `!bot status`

The bot will now use environment variables instead of hardcoded values, improving security and maintainability.

## Support

For issues or questions:
1. Check the logs: `docker-compose logs matrix-bot`
2. Verify `.env` file configuration
3. Test Matrix homeserver connectivity
4. Review room permissions and access

## License

This bot is part of the acebuddy.quest homelab infrastructure.