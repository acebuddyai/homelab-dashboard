# Matrix Bot Server Monitoring Guide

## Overview
The Matrix bot has been enhanced with comprehensive server monitoring capabilities. It can now provide real-time information about CPU usage, memory consumption, disk space, network statistics, temperature sensors, and GPU information.

## New Commands

### Basic Server Overview
- `!bot server` - Complete server overview with key metrics
- `!bot help` - Updated help menu showing all available commands

### Detailed Information
- `!bot cpu` - CPU usage, core count, and frequency
- `!bot memory` - Memory and swap usage statistics
- `!bot disk` - Disk space usage for root filesystem
- `!bot network` - Network I/O statistics (bytes and packets)
- `!bot temp` - Temperature sensor readings (if available)
- `!bot gpu` - GPU information including load, memory, and temperature

## Features

### System Metrics
- **CPU**: Usage percentage, core count, frequency
- **Memory**: Used/available/total RAM, swap usage
- **Disk**: Used/free/total space with percentages
- **Network**: Bytes and packets sent/received
- **System**: Hostname, platform, uptime, boot time

### Temperature Monitoring
- Automatically detects available temperature sensors
- Displays readings from all detected sensors
- Graceful fallback if no sensors are available

### GPU Monitoring
- Supports NVIDIA GPUs via GPUtil
- Shows GPU load, memory usage, and temperature
- Graceful fallback if no GPU is detected

### User-Friendly Output
- Formatted output with emojis and clear sections
- Human-readable byte formatting (B, KB, MB, GB, TB)
- Percentage calculations for usage metrics
- Error handling with informative messages

## Dependencies Added

The following Python packages have been added to `requirements.txt`:
- `psutil>=5.9.0` - System and process monitoring
- `GPUtil>=1.4.0` - GPU monitoring (NVIDIA)

## Deployment

### 1. Rebuild the Bot Container
```bash
cd homelab/matrix
docker-compose down matrix-bot
docker-compose up --build -d matrix-bot
```

### 2. Verify Deployment
```bash
# Check container status
docker ps | grep matrix-bot

# Monitor logs
docker logs -f matrix-bot

# Look for successful startup messages
docker logs matrix-bot 2>&1 | grep -E "(online|Started|Successfully)"
```

### 3. Test the New Features
In your Matrix room, try these commands:
```
!bot help
!bot server
!bot cpu
!bot memory
!bot disk
!bot network
!bot temp
!bot gpu
```

## Troubleshooting

### Common Issues

1. **Temperature sensors not available**
   - This is normal on some systems/containers
   - The bot will show "N/A" and continue functioning

2. **GPU monitoring unavailable**
   - Expected if no NVIDIA GPU is present
   - The bot will gracefully handle this

3. **Permission issues**
   - The bot runs as a non-root user for security
   - Some system information may be limited in containers

### Checking Logs
```bash
# Real-time logs
docker logs -f matrix-bot

# Recent logs
docker logs --tail 50 matrix-bot

# Error logs only
docker logs matrix-bot 2>&1 | grep -i error
```

### Container Shell Access
```bash
# Access container for debugging
docker exec -it matrix-bot /bin/bash

# Test monitoring functions directly
python3 -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"
```

## Security Considerations

- All monitoring data is read-only system information
- No sensitive data is exposed through the monitoring commands
- The bot continues to run with minimal privileges
- Environment variables remain properly secured

## Performance Impact

- Monitoring commands have minimal performance impact
- CPU monitoring uses a 1-second interval for accuracy
- All operations are asynchronous and non-blocking
- No continuous monitoring - data is gathered on-demand

## Example Output

### Server Overview (`!bot server`)
```
🖥️ **Server Overview:**
• Hostname: homelab-server
• Platform: Linux-5.15.0-72-generic-x86_64-with-glibc2.35
• Uptime: 2 days, 14:32:15
• CPU Usage: 15.2% (8 cores)
• Memory: 4.2 GB/16.0 GB (26.3%)
• Disk: 245.8 GB/931.5 GB (26.4%)
• Network: ↑2.1 GB ↓15.7 GB
• Temperature: coretemp_Package id 0: 45°C
```

### CPU Information (`!bot cpu`)
```
🖥️ **CPU Information:**
• Usage: 15.2%
• Cores: 8
• Frequency: 2400 MHz
```

### Memory Information (`!bot memory`)
```
💾 **Memory Information:**
• Used: 4.2 GB (26.3%)
• Available: 11.8 GB
• Total: 16.0 GB
• Swap Used: 0.0 B (0.0%)
• Swap Total: 2.0 GB
```

## Future Enhancements

Potential future additions:
- Process monitoring (top processes by CPU/memory)
- Service status checking
- Custom alerts for threshold breaches
- Historical data trending
- Docker container monitoring
- Custom monitoring intervals