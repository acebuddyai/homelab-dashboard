#!/usr/bin/env python3
"""
Enhanced Matrix Bot with proper encryption support and LLM integration for acebuddy.quest homeserver
"""

import asyncio
import logging
import os
import platform
import datetime
import socket
import psutil
import aiohttp
import json
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, JoinResponse, MegolmEvent
from nio.crypto import TrustState

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class EnhancedMatrixBot:
    def __init__(self):
        # Configuration from environment variables
        self.homeserver_url = os.getenv("MATRIX_HOMESERVER_URL")
        self.username = os.getenv("MATRIX_BOT_USERNAME")
        self.password = os.getenv("MATRIX_BOT_PASSWORD")
        self.target_room_id = os.getenv("MATRIX_TARGET_ROOM_ID")
        self.store_path = os.getenv("BOT_STORE_DIR", "/app/store")

        # LLM Configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://172.20.0.30:11434")
        self.llm_models = [
            {"name": "llama3.2:latest", "display": "Llama 3.2 (Default)"}
        ]

        # Validate required configuration
        if not all([self.homeserver_url, self.username, self.password, self.target_room_id]):
            raise ValueError("Missing required environment variables. Please check .env file.")

        # Create client WITH encryption store for encrypted rooms
        self.client = AsyncClient(
            homeserver=self.homeserver_url,
            user=self.username,
            store_path=self.store_path
        )

        # Add callbacks for both encrypted and unencrypted messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.encrypted_message_callback, MegolmEvent)

    async def login(self):
        """Login to Matrix server"""
        try:
            # Load store if it exists
            if os.path.exists(os.path.join(self.store_path, "next_batch")):
                self.client.load_store()
                logger.info("📂 Loaded store from disk")

            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"❌ Login failed: {response}")
                return False

            logger.info(f"✅ Logged in as {self.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    async def join_room(self, room_id):
        """Join the target room"""
        try:
            response = await self.client.join(room_id)
            if isinstance(response, JoinResponse):
                logger.info(f"✅ Joined room: {room_id}")
                return True
            else:
                logger.error(f"❌ Failed to join room: {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Room join error: {e}")
            return False

    async def send_message(self, room_id, message):
        """Send message to room"""
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message},
                ignore_unverified_devices=True
            )
        except Exception as e:
            logger.error(f"❌ Send message error: {e}")

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle unencrypted messages"""
        if event.sender == self.client.user_id:
            return

        logger.info(f"💬 Message from {event.sender}: {event.body[:50]}...")
        await self.process_command(room, event.sender, event.body)

    async def encrypted_message_callback(self, room: MatrixRoom, event: MegolmEvent):
        """Handle encrypted messages"""
        if event.sender == self.client.user_id:
            return

        try:
            decrypted_event = await self.client.decrypt_event(event)
            if hasattr(decrypted_event, 'body'):
                logger.info(f"🔐 Encrypted message from {event.sender}: {decrypted_event.body[:50]}...")
                await self.process_command(room, event.sender, decrypted_event.body)
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")

    async def get_server_stats(self):
        """Get comprehensive system statistics"""
        try:
            stats = {
                'system': {
                    'hostname': socket.gethostname(),
                    'platform': f"{platform.system()} {platform.release()}",
                    'uptime': str(datetime.timedelta(seconds=int(psutil.boot_time()))),
                },
                'cpu': {
                    'usage': psutil.cpu_percent(interval=1),
                    'cores': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                },
                'memory': dict(psutil.virtual_memory()._asdict()),
                'swap': dict(psutil.swap_memory()._asdict()),
                'disk': dict(psutil.disk_usage('/')._asdict()),
                'network': dict(psutil.net_io_counters()._asdict()),
                'temperatures': {},
                'gpu': []
            }

            # Temperature sensors
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            label = entry.label or name
                            stats['temperatures'][label] = entry.current
            except Exception:
                pass

            # GPU information
            if GPU_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    for gpu in gpus:
                        stats['gpu'].append({
                            'name': gpu.name,
                            'load': f"{gpu.load*100:.1f}%",
                            'memory': f"{gpu.memoryUsed}MB/{gpu.memoryTotal}MB",
                            'temp': f"{gpu.temperature}°C" if gpu.temperature else "N/A"
                        })
                except Exception:
                    pass

            return stats
        except Exception as e:
            logger.error(f"❌ Stats error: {e}")
            return None

    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"

    async def query_ollama(self, model, prompt, max_words=100):
        """Query Ollama API"""
        try:
            data = {
                "model": model,
                "prompt": f"{prompt}\n\nPlease keep your response to {max_words} words or less.",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": max_words * 2  # Rough estimate
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', 'No response received')
                    else:
                        return f"Error: HTTP {response.status}"
        except asyncio.TimeoutError:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    async def process_command(self, room: MatrixRoom, sender: str, message_body: str):
        """Process bot commands from either encrypted or unencrypted messages"""
        command = message_body.strip()
        sender_name = sender.split(':')[0][1:]  # Extract username

        # Bot commands (bbot/Bbot)
        if command.lower().startswith("bbot"):
            await self.handle_bot_command(room, sender_name, command)

        # AI commands (aai/Aai)
        elif command.lower().startswith("aai"):
            await self.handle_ai_command(room, sender_name, command)

    async def handle_bot_command(self, room: MatrixRoom, sender_name: str, command: str):
        """Handle bot system commands"""
        cmd = command.lower()
        logger.info(f"🤖 Processing bot command: {cmd}")

        if cmd == "bbot help":
            help_text = """🤖 **Bot Commands:**
• bbot help - Show this help
• bbot ping - Test response
• bbot info - Bot information
• bbot status - Bot status
• bbot server - Server system stats
• bbot cpu - CPU information
• bbot memory - Memory usage
• bbot disk - Disk usage
• bbot network - Network statistics
• bbot temp - Temperature sensors
• bbot gpu - GPU information (if available)
• bbot echo <text> - Echo your message
• bbot room - Room information"""
            await self.send_message(room.room_id, help_text)

        elif cmd == "bbot ping":
            await self.send_message(room.room_id, f"Pong! 🏓 Hello {sender_name}!")

        elif cmd == "bbot info":
            info_text = f"""📊 **Bot Information:**
• Bot: {self.username}
• Room: {room.display_name or 'Unknown'}
• Users: {len(room.users)}
• Encrypted: {'Yes' if room.encrypted else 'No'}
• Store: {self.store_path}"""
            await self.send_message(room.room_id, info_text)

        elif cmd == "bbot status":
            room_count = len(self.client.rooms)
            await self.send_message(room.room_id, f"✅ Bot is running and healthy!\n📊 Connected to {room_count} rooms\n🔐 Encryption: {'Enabled' if self.client.olm else 'Disabled'}")

        elif cmd.startswith("bbot echo "):
            echo_text = command[10:].strip()  # Remove "bbot echo "
            if echo_text:
                await self.send_message(room.room_id, f"🔊 Echo: {echo_text}")
            else:
                await self.send_message(room.room_id, "❌ Please provide text to echo!")

        elif cmd == "bbot server":
            stats = await self.get_server_stats()
            if stats:
                server_info = f"""🖥️ **Server Overview:**
• Hostname: {stats['system']['hostname']}
• Platform: {stats['system']['platform']}
• Uptime: {stats['system']['uptime']}
• CPU Usage: {stats['cpu']['usage']:.1f}% ({stats['cpu']['cores']} cores)
• Memory: {self.format_bytes(stats['memory']['used'])}/{self.format_bytes(stats['memory']['total'])} ({stats['memory']['percent']:.1f}%)
• Disk: {self.format_bytes(stats['disk']['used'])}/{self.format_bytes(stats['disk']['total'])} ({stats['disk']['percent']:.1f}%)
• Network: ↑{self.format_bytes(stats['network']['bytes_sent'])} ↓{self.format_bytes(stats['network']['bytes_recv'])}"""

                if stats['temperatures']:
                    temp_str = ", ".join([f"{k}: {v}°C" for k, v in stats['temperatures'].items() if isinstance(v, (int, float))])
                    if temp_str:
                        server_info += f"\n• Temperature: {temp_str}"

                if stats['gpu']:
                    gpu_str = ", ".join([f"{gpu['name']}: {gpu['load']} load, {gpu['temp']}" for gpu in stats['gpu']])
                    server_info += f"\n• GPU: {gpu_str}"

                await self.send_message(room.room_id, server_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve server statistics")

        elif cmd == "bbot cpu":
            stats = await self.get_server_stats()
            if stats:
                cpu_info = f"""🖥️ **CPU Information:**
• Usage: {stats['cpu']['usage']:.1f}%
• Cores: {stats['cpu']['cores']}
• Frequency: {stats['cpu']['frequency']:.0f} MHz""" if stats['cpu']['frequency'] else f"""🖥️ **CPU Information:**
• Usage: {stats['cpu']['usage']:.1f}%
• Cores: {stats['cpu']['cores']}
• Frequency: N/A"""
                await self.send_message(room.room_id, cpu_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve CPU information")

        elif cmd == "bbot memory":
            stats = await self.get_server_stats()
            if stats:
                memory_info = f"""💾 **Memory Information:**
• Used: {self.format_bytes(stats['memory']['used'])} ({stats['memory']['percent']:.1f}%)
• Available: {self.format_bytes(stats['memory']['available'])}
• Total: {self.format_bytes(stats['memory']['total'])}
• Swap Used: {self.format_bytes(stats['swap']['used'])} ({stats['swap']['percent']:.1f}%)
• Swap Total: {self.format_bytes(stats['swap']['total'])}"""
                await self.send_message(room.room_id, memory_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve memory information")

        elif cmd == "bbot disk":
            stats = await self.get_server_stats()
            if stats:
                disk_info = f"""💿 **Disk Information:**
• Used: {self.format_bytes(stats['disk']['used'])} ({stats['disk']['percent']:.1f}%)
• Free: {self.format_bytes(stats['disk']['total'] - stats['disk']['used'])}
• Total: {self.format_bytes(stats['disk']['total'])}"""
                await self.send_message(room.room_id, disk_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve disk information")

        elif cmd == "bbot network":
            stats = await self.get_server_stats()
            if stats:
                network_info = f"""🌐 **Network Information:**
• Bytes Sent: {self.format_bytes(stats['network']['bytes_sent'])}
• Bytes Received: {self.format_bytes(stats['network']['bytes_recv'])}
• Packets Sent: {stats['network']['packets_sent']:,}
• Packets Received: {stats['network']['packets_recv']:,}"""
                await self.send_message(room.room_id, network_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve network information")

        elif cmd == "bbot temp":
            stats = await self.get_server_stats()
            if stats and stats['temperatures']:
                temp_readings = []
                for sensor, temp in stats['temperatures'].items():
                    if isinstance(temp, (int, float)):
                        temp_readings.append(f"• {sensor}: {temp}°C")
                    else:
                        temp_readings.append(f"• {sensor}: {temp}")

                if temp_readings:
                    temp_info = "🌡️ **Temperature Sensors:**\n" + "\n".join(temp_readings)
                else:
                    temp_info = "🌡️ **Temperature Sensors:** No temperature sensors detected"
                await self.send_message(room.room_id, temp_info)
            else:
                await self.send_message(room.room_id, "❌ Unable to retrieve temperature information")

        elif cmd == "bbot gpu":
            stats = await self.get_server_stats()
            if stats and stats['gpu']:
                gpu_info = "🎮 **GPU Information:**\n"
                for i, gpu in enumerate(stats['gpu'], 1):
                    gpu_info += f"• GPU {i}: {gpu['name']}\n"
                    gpu_info += f"  - Load: {gpu['load']}\n"
                    gpu_info += f"  - Memory: {gpu['memory']}\n"
                    gpu_info += f"  - Temperature: {gpu['temp']}\n"
                await self.send_message(room.room_id, gpu_info)
            else:
                await self.send_message(room.room_id, "🎮 **GPU Information:** No GPU detected or GPU monitoring unavailable")

        elif cmd == "bbot room":
            member_count = len(room.users)
            room_info = f"""🏠 **Room Information:**
• Name: {room.display_name or 'No name set'}
• Room ID: {room.room_id}
• Members: {member_count}
• Topic: {room.topic or 'No topic set'}
• Encrypted: {'Yes' if room.encrypted else 'No'}
• Power Level: {room.power_levels.get(self.client.user_id, 0)}"""
            await self.send_message(room.room_id, room_info)

        else:
            await self.send_message(room.room_id, f"❓ Unknown command: {command}\nTry 'bbot help' for available commands.")

    async def handle_ai_command(self, room: MatrixRoom, sender_name: str, command: str):
        """Handle AI/LLM commands"""
        cmd_parts = command.split()
        cmd_lower = command.lower()

        logger.info(f"🧠 Processing AI command: {command}")

        if cmd_lower == "aai help" or cmd_lower == "aai":
            help_text = """🧠 **AI Commands:**
• aai help - Show this help
• aai <prompt> - Send prompt to default LLM
• aai 1 <prompt> - Send to Llama 3.2 (Default)

**Available Models:**"""

            for i, model in enumerate(self.llm_models, 1):
                help_text += f"\n{i}. {model['display']}"

            help_text += "\n\n*Responses are limited to 100 words*"
            await self.send_message(room.room_id, help_text)
            return

        # Check if user specified a model number
        model_index = 0  # Default to first model
        prompt_start = 1  # Start of prompt in cmd_parts

        if len(cmd_parts) >= 2 and cmd_parts[1].isdigit():
            requested_model = int(cmd_parts[1]) - 1
            if 0 <= requested_model < len(self.llm_models):
                model_index = requested_model
                prompt_start = 2
            else:
                await self.send_message(room.room_id, f"❌ Invalid model number. Use 'aai help' to see available models.")
                return

        # Extract the prompt
        if len(cmd_parts) <= prompt_start:
            await self.send_message(room.room_id, "❌ Please provide a prompt. Example: `aai What is the weather like?`")
            return

        prompt = " ".join(cmd_parts[prompt_start:])
        selected_model = self.llm_models[model_index]

        # Send "processing" message
        processing_msg = f"🧠 Sending your prompt to {selected_model['display']}..."
        await self.send_message(room.room_id, processing_msg)

        # Query the LLM
        response = await self.query_ollama(selected_model["name"], prompt, max_words=100)

        # Send response
        final_msg = f"""🧠 **{selected_model['display']} Response:**

{response}

*({len(response.split())} words)*"""

        await self.send_message(room.room_id, final_msg)

    async def trust_all_devices(self):
        """Trust all devices for encryption"""
        try:
            for user_id, device_dict in self.client.device_store.items():
                for device in device_dict.values():
                    if device.trust_state == TrustState.unset:
                        self.client.verify_device(device)
            logger.info("🔐 Trusted all devices")
        except Exception as e:
            logger.error(f"❌ Device trust error: {e}")

    async def start(self):
        """Start the bot"""
        logger.info("🚀 Starting Enhanced Matrix Bot...")

        # Create store directory
        os.makedirs(self.store_path, exist_ok=True)

        # Login
        if not await self.login():
            logger.error("❌ Failed to login, exiting")
            return

        # Trust devices for encryption
        await self.trust_all_devices()

        # Join target room
        if await self.join_room(self.target_room_id):
            await asyncio.sleep(2)
            greeting = f"🤖 Bot online! Commands: 'bbot help' for system info, 'aai help' for AI chat"
            await self.send_message(self.target_room_id, greeting)

        # Start syncing
        logger.info("🔄 Starting sync...")
        await self.client.sync_forever(timeout=30000)

    async def close(self):
        """Close client connection"""
        try:
            await self.client.close()
            logger.info("👋 Bot connection closed")
        except Exception as e:
            logger.error(f"❌ Close error: {e}")

async def main():
    """Main function"""
    logger.info("🚀 Initializing Enhanced Matrix Bot...")

    bot = EnhancedMatrixBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("⛔ Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
