#!/usr/bin/env python3
"""
Simplified Matrix Bot for acebuddy.quest homeserver
This version handles encryption more gracefully
"""

import asyncio
import logging
import os
from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, JoinResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SimpleMatrixBot:
    def __init__(self):
        # Configuration from environment variables
        self.homeserver_url = os.getenv("MATRIX_HOMESERVER_URL", "https://matrix.acebuddy.quest")
        self.username = os.getenv("MATRIX_BOT_USERNAME")
        self.password = os.getenv("MATRIX_BOT_PASSWORD")
        self.target_room_id = os.getenv("MATRIX_TARGET_ROOM_ID")

        # Validate required environment variables
        if not all([self.username, self.password, self.target_room_id]):
            raise ValueError("Missing required environment variables: MATRIX_BOT_USERNAME, MATRIX_BOT_PASSWORD, MATRIX_TARGET_ROOM_ID")

        # Create client without encryption store for simplicity
        self.client = AsyncClient(
            homeserver=self.homeserver_url,
            user=self.username
        )

        # Add callback for messages
        self.client.add_event_callback(self.message_callback, RoomMessageText)

    async def login(self):
        """Login to the Matrix homeserver"""
        try:
            response = await self.client.login(self.password)
            if isinstance(response, LoginResponse):
                logger.info(f"Successfully logged in as {self.username}")
                return True
            else:
                logger.error(f"Failed to login: {response}")
                return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def join_room(self, room_id):
        """Join a Matrix room"""
        try:
            response = await self.client.join(room_id)
            if isinstance(response, JoinResponse):
                logger.info(f"Successfully joined room: {room_id}")
                return True
            else:
                logger.error(f"Failed to join room {room_id}: {response}")
                return False
        except Exception as e:
            logger.error(f"Error joining room {room_id}: {e}")
            return False

    async def send_message(self, room_id, message):
        """Send a message to a room with encryption handling"""
        try:
            # Simple message content
            content = {
                "msgtype": "m.text",
                "body": message
            }

            # Try to send with ignore_unverified_devices for encrypted rooms
            response = await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content,
                ignore_unverified_devices=True
            )

            logger.info(f"Sent message to {room_id}: {message[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages"""
        # Ignore messages from the bot itself
        if event.sender == self.client.user_id:
            return

        logger.info(f"Message from {event.sender} in {room.display_name}: {event.body}")

        # Handle commands
        if event.body.startswith("!bot"):
            await self.handle_command(room, event)

    async def handle_command(self, room: MatrixRoom, event: RoomMessageText):
        """Handle bot commands"""
        command = event.body.strip().lower()
        sender = event.sender.split(':')[0][1:]  # Extract username

        if command == "!bot help":
            help_text = """🤖 Bot Commands:
• !bot help - Show this help
• !bot ping - Test response
• !bot info - Bot information
• !bot status - Bot status
• !bot echo <text> - Echo your message"""
            await self.send_message(room.room_id, help_text)

        elif command == "!bot ping":
            await self.send_message(room.room_id, f"Pong! 🏓 Hello {sender}!")

        elif command == "!bot info":
            info_text = f"""📊 Bot Info:
• Bot: {self.username}
• Room: {room.display_name}
• Users: {len(room.users)}
• Encrypted: {'Yes' if room.encrypted else 'No'}"""
            await self.send_message(room.room_id, info_text)

        elif command == "!bot status":
            await self.send_message(room.room_id, "✅ Bot is running and healthy!")

        elif command.startswith("!bot echo "):
            echo_text = event.body[10:].strip()  # Remove "!bot echo "
            if echo_text:
                await self.send_message(room.room_id, f"🔊 {echo_text}")
            else:
                await self.send_message(room.room_id, "❌ Please provide text to echo!")

        else:
            await self.send_message(room.room_id, "❓ Unknown command. Try '!bot help'")

    async def start(self):
        """Start the bot"""
        logger.info("🤖 Starting Simple Matrix Bot...")

        # Login
        if not await self.login():
            logger.error("❌ Failed to login")
            return

        # Join target room
        if await self.join_room(self.target_room_id):
            # Wait a moment for room to be ready
            await asyncio.sleep(3)
            # Send greeting
            greeting = "🤖 Hello! I'm your simple Matrix bot. Type '!bot help' for commands!"
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
            logger.error(f"Error closing: {e}")

async def main():
    """Main function"""
    bot = SimpleMatrixBot()

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
