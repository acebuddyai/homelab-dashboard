#!/usr/bin/env python3
"""
Enhanced Matrix Bot with proper encryption support for acebuddy.quest homeserver
"""

import asyncio
import logging
import os
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
        """Login to the Matrix homeserver"""
        try:
            # Try to restore login from store first
            if os.path.exists(os.path.join(self.store_path, "next_batch")):
                logger.info("🔄 Attempting to restore login from store...")
                self.client.load_store()

            # Login if we don't have an access token
            if not self.client.access_token:
                response = await self.client.login(self.password)
                if isinstance(response, LoginResponse):
                    logger.info(f"✅ Successfully logged in as {self.username}")
                else:
                    logger.error(f"❌ Failed to login: {response}")
                    return False
            else:
                logger.info("✅ Restored login from store")

            # Configure encryption settings after login
            if self.client.olm:
                # Trust all devices by default for this bot
                self.client.olm.verify_keys = False
                logger.info("🔐 Encryption configured")

            return True
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    async def join_room(self, room_id):
        """Join a Matrix room"""
        try:
            response = await self.client.join(room_id)
            if isinstance(response, JoinResponse):
                logger.info(f"✅ Successfully joined room: {room_id}")
                return True
            else:
                logger.error(f"❌ Failed to join room {room_id}: {response}")
                return False
        except Exception as e:
            logger.error(f"❌ Error joining room {room_id}: {e}")
            return False

    async def send_message(self, room_id, message):
        """Send a message to a room with encryption handling"""
        try:
            content = {
                "msgtype": "m.text",
                "body": message
            }

            response = await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content,
                ignore_unverified_devices=True
            )

            logger.info(f"📤 Sent message to {room_id}: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return False

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming unencrypted messages"""
        # Ignore messages from the bot itself
        if event.sender == self.client.user_id:
            return

        logger.info(f"📨 Unencrypted message from {event.sender}: {event.body}")
        await self.process_command(room, event.sender, event.body)

    async def encrypted_message_callback(self, room: MatrixRoom, event: MegolmEvent):
        """Handle incoming encrypted messages"""
        try:
            # Try to decrypt the message
            decrypted_event = await self.client.decrypt_event(event)

            if decrypted_event and hasattr(decrypted_event, 'body'):
                # Ignore messages from the bot itself
                if decrypted_event.sender == self.client.user_id:
                    return

                logger.info(f"🔓 Decrypted message from {decrypted_event.sender}: {decrypted_event.body}")
                await self.process_command(room, decrypted_event.sender, decrypted_event.body)
            else:
                logger.warning(f"⚠️ Could not decrypt message from {event.sender}")

        except Exception as e:
            logger.error(f"❌ Error decrypting message: {e}")

    async def process_command(self, room: MatrixRoom, sender: str, message_body: str):
        """Process bot commands from either encrypted or unencrypted messages"""
        if not message_body.startswith("!bot"):
            return

        command = message_body.strip().lower()
        sender_name = sender.split(':')[0][1:]  # Extract username

        logger.info(f"🤖 Processing command: {command}")

        if command == "!bot help":
            help_text = """🤖 **Bot Commands:**
• !bot help - Show this help
• !bot ping - Test response
• !bot info - Bot information
• !bot status - Bot status
• !bot echo <text> - Echo your message
• !bot room - Room information"""
            await self.send_message(room.room_id, help_text)

        elif command == "!bot ping":
            await self.send_message(room.room_id, f"Pong! 🏓 Hello {sender_name}!")

        elif command == "!bot info":
            info_text = f"""📊 **Bot Information:**
• Bot: {self.username}
• Room: {room.display_name or 'Unknown'}
• Users: {len(room.users)}
• Encrypted: {'Yes' if room.encrypted else 'No'}
• Store: {self.store_path}"""
            await self.send_message(room.room_id, info_text)

        elif command == "!bot status":
            room_count = len(self.client.rooms)
            await self.send_message(room.room_id, f"✅ Bot is running and healthy!\n📊 Connected to {room_count} rooms\n🔐 Encryption: {'Enabled' if self.client.olm else 'Disabled'}")

        elif command.startswith("!bot echo "):
            echo_text = message_body[10:].strip()  # Remove "!bot echo "
            if echo_text:
                await self.send_message(room.room_id, f"🔊 Echo: {echo_text}")
            else:
                await self.send_message(room.room_id, "❌ Please provide text to echo!")

        elif command == "!bot room":
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
            await self.send_message(room.room_id, f"❓ Unknown command: {command}\nTry '!bot help' for available commands.")

    async def trust_all_devices(self):
        """Trust all devices in the room for encryption"""
        try:
            if not self.client.olm:
                return

            # Get the target room
            room = self.client.rooms.get(self.target_room_id)
            if not room:
                return

            for user_id in room.users:
                # Get devices for this user
                user_devices = self.client.device_store.active_user_devices.get(user_id, {})
                for device_id, device in user_devices.items():
                    if device.trust_state != TrustState.verified:
                        self.client.verify_device(device)
                        logger.info(f"🔐 Trusted device {device_id} for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Error trusting devices: {e}")

    async def start(self):
        """Start the bot"""
        logger.info("🚀 Starting Enhanced Matrix Bot...")

        # Create store directory
        os.makedirs(self.store_path, exist_ok=True)

        # Login
        if not await self.login():
            logger.error("❌ Failed to login")
            return

        # Join target room
        if await self.join_room(self.target_room_id):
            # Wait for room to be ready and trust devices
            await asyncio.sleep(2)
            await self.trust_all_devices()

            # Send greeting
            greeting = "🤖 Enhanced Matrix bot online! I can handle encrypted messages. Type '!bot help' for commands!"
            await self.send_message(self.target_room_id, greeting)

        # Start syncing
        logger.info("🔄 Starting sync...")
        try:
            await self.client.sync_forever(timeout=30000)
        except Exception as e:
            logger.error(f"❌ Sync error: {e}")
            raise

    async def close(self):
        """Close the client"""
        try:
            await self.client.close()
            logger.info("👋 Bot connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing: {e}")

async def main():
    """Main function"""
    bot = EnhancedMatrixBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
