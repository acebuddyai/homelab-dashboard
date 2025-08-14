#!/usr/bin/env python3
"""
Test script for server monitoring functionality
"""

import asyncio
import platform
import datetime
import socket
import psutil
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("⚠️ GPUtil not available - GPU monitoring disabled")

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

async def get_server_stats():
    """Get comprehensive server statistics"""
    try:
        print("🔍 Gathering server statistics...")

        # CPU Information
        print("  📊 Getting CPU info...")
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory Information
        print("  💾 Getting memory info...")
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Disk Information
        print("  💿 Getting disk info...")
        disk = psutil.disk_usage('/')

        # Network Information
        print("  🌐 Getting network info...")
        net_io = psutil.net_io_counters()

        # System Information
        print("  🖥️ Getting system info...")
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time

        # Temperature (if available)
        print("  🌡️ Getting temperature info...")
        temps = {}
        try:
            temp_sensors = psutil.sensors_temperatures()
            for name, entries in temp_sensors.items():
                for entry in entries:
                    if entry.current:
                        temps[f"{name}_{entry.label or 'temp'}"] = entry.current
        except Exception as e:
            print(f"    ⚠️ Temperature sensors not available: {e}")
            temps = {"temp": "N/A"}

        # GPU Information (if available)
        print("  🎮 Getting GPU info...")
        gpu_info = []
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpu_info.append({
                        'name': gpu.name,
                        'load': f"{gpu.load * 100:.1f}%",
                        'memory': f"{gpu.memoryUsed}/{gpu.memoryTotal}MB",
                        'temp': f"{gpu.temperature}°C"
                    })
            except Exception as e:
                print(f"    ⚠️ GPU info not available: {e}")
        else:
            print("    ⚠️ GPU monitoring not available")

        return {
            'cpu': {
                'usage': cpu_percent,
                'cores': cpu_count,
                'frequency': cpu_freq.current if cpu_freq else None
            },
            'memory': {
                'used': memory.used,
                'total': memory.total,
                'percent': memory.percent,
                'available': memory.available
            },
            'swap': {
                'used': swap.used,
                'total': swap.total,
                'percent': swap.percent
            },
            'disk': {
                'used': disk.used,
                'total': disk.total,
                'percent': (disk.used / disk.total) * 100
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            },
            'system': {
                'uptime': str(uptime).split('.')[0],
                'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
                'hostname': socket.gethostname(),
                'platform': platform.platform()
            },
            'temperatures': temps,
            'gpu': gpu_info
        }
    except Exception as e:
        print(f"❌ Error getting server stats: {e}")
        return None

def print_stats(stats):
    """Print formatted server statistics"""
    if not stats:
        print("❌ No statistics available")
        return

    print("\n" + "="*60)
    print("🖥️  SERVER STATISTICS")
    print("="*60)

    # System Info
    print(f"\n📋 SYSTEM INFORMATION:")
    print(f"   Hostname: {stats['system']['hostname']}")
    print(f"   Platform: {stats['system']['platform']}")
    print(f"   Uptime: {stats['system']['uptime']}")
    print(f"   Boot Time: {stats['system']['boot_time']}")

    # CPU Info
    print(f"\n🖥️  CPU INFORMATION:")
    print(f"   Usage: {stats['cpu']['usage']:.1f}%")
    print(f"   Cores: {stats['cpu']['cores']}")
    if stats['cpu']['frequency']:
        print(f"   Frequency: {stats['cpu']['frequency']:.0f} MHz")
    else:
        print(f"   Frequency: N/A")

    # Memory Info
    print(f"\n💾 MEMORY INFORMATION:")
    print(f"   Used: {format_bytes(stats['memory']['used'])} ({stats['memory']['percent']:.1f}%)")
    print(f"   Available: {format_bytes(stats['memory']['available'])}")
    print(f"   Total: {format_bytes(stats['memory']['total'])}")
    print(f"   Swap Used: {format_bytes(stats['swap']['used'])} ({stats['swap']['percent']:.1f}%)")
    print(f"   Swap Total: {format_bytes(stats['swap']['total'])}")

    # Disk Info
    print(f"\n💿 DISK INFORMATION:")
    print(f"   Used: {format_bytes(stats['disk']['used'])} ({stats['disk']['percent']:.1f}%)")
    print(f"   Free: {format_bytes(stats['disk']['total'] - stats['disk']['used'])}")
    print(f"   Total: {format_bytes(stats['disk']['total'])}")

    # Network Info
    print(f"\n🌐 NETWORK INFORMATION:")
    print(f"   Bytes Sent: {format_bytes(stats['network']['bytes_sent'])}")
    print(f"   Bytes Received: {format_bytes(stats['network']['bytes_recv'])}")
    print(f"   Packets Sent: {stats['network']['packets_sent']:,}")
    print(f"   Packets Received: {stats['network']['packets_recv']:,}")

    # Temperature Info
    print(f"\n🌡️  TEMPERATURE SENSORS:")
    if stats['temperatures']:
        for sensor, temp in stats['temperatures'].items():
            if isinstance(temp, (int, float)):
                print(f"   {sensor}: {temp}°C")
            else:
                print(f"   {sensor}: {temp}")
    else:
        print("   No temperature sensors detected")

    # GPU Info
    print(f"\n🎮 GPU INFORMATION:")
    if stats['gpu']:
        for i, gpu in enumerate(stats['gpu'], 1):
            print(f"   GPU {i}: {gpu['name']}")
            print(f"     Load: {gpu['load']}")
            print(f"     Memory: {gpu['memory']}")
            print(f"     Temperature: {gpu['temp']}")
    else:
        print("   No GPU detected or GPU monitoring unavailable")

async def test_bot_commands():
    """Test the formatted output that would be sent to Matrix"""
    stats = await get_server_stats()
    if not stats:
        return

    print("\n" + "="*60)
    print("🤖 BOT COMMAND OUTPUTS")
    print("="*60)

    # Server overview
    print(f"\n!bot server output:")
    print("-" * 40)
    server_info = f"""🖥️ **Server Overview:**
• Hostname: {stats['system']['hostname']}
• Platform: {stats['system']['platform']}
• Uptime: {stats['system']['uptime']}
• CPU Usage: {stats['cpu']['usage']:.1f}% ({stats['cpu']['cores']} cores)
• Memory: {format_bytes(stats['memory']['used'])}/{format_bytes(stats['memory']['total'])} ({stats['memory']['percent']:.1f}%)
• Disk: {format_bytes(stats['disk']['used'])}/{format_bytes(stats['disk']['total'])} ({stats['disk']['percent']:.1f}%)
• Network: ↑{format_bytes(stats['network']['bytes_sent'])} ↓{format_bytes(stats['network']['bytes_recv'])}"""

    if stats['temperatures']:
        temp_str = ", ".join([f"{k}: {v}°C" for k, v in stats['temperatures'].items() if isinstance(v, (int, float))])
        if temp_str:
            server_info += f"\n• Temperature: {temp_str}"

    if stats['gpu']:
        gpu_str = ", ".join([f"{gpu['name']}: {gpu['load']} load, {gpu['temp']}" for gpu in stats['gpu']])
        server_info += f"\n• GPU: {gpu_str}"

    print(server_info)

    # CPU command
    print(f"\n!bot cpu output:")
    print("-" * 40)
    cpu_info = f"""🖥️ **CPU Information:**
• Usage: {stats['cpu']['usage']:.1f}%
• Cores: {stats['cpu']['cores']}"""
    if stats['cpu']['frequency']:
        cpu_info += f"\n• Frequency: {stats['cpu']['frequency']:.0f} MHz"
    else:
        cpu_info += f"\n• Frequency: N/A"
    print(cpu_info)

    # Memory command
    print(f"\n!bot memory output:")
    print("-" * 40)
    memory_info = f"""💾 **Memory Information:**
• Used: {format_bytes(stats['memory']['used'])} ({stats['memory']['percent']:.1f}%)
• Available: {format_bytes(stats['memory']['available'])}
• Total: {format_bytes(stats['memory']['total'])}
• Swap Used: {format_bytes(stats['swap']['used'])} ({stats['swap']['percent']:.1f}%)
• Swap Total: {format_bytes(stats['swap']['total'])}"""
    print(memory_info)

async def main():
    """Main test function"""
    print("🚀 Testing Matrix Bot Server Monitoring")
    print("=" * 60)

    # Test dependencies
    print("\n📦 Checking dependencies...")
    try:
        import psutil
        print("  ✅ psutil - OK")
    except ImportError:
        print("  ❌ psutil - MISSING")
        return

    try:
        import GPUtil
        print("  ✅ GPUtil - OK")
    except ImportError:
        print("  ⚠️ GPUtil - MISSING (GPU monitoring disabled)")

    # Get and display stats
    stats = await get_server_stats()
    print_stats(stats)

    # Test bot command outputs
    await test_bot_commands()

    print("\n" + "="*60)
    print("✅ Test completed successfully!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
