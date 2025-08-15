#!/usr/bin/env python3
"""
Simple Matrix Bot for acebuddy.quest homeserver
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, JoinResponse, Event
from config import BotConfig

# Set up logging
logging.basicConfig(
    level=getattr(logging, BotConfig.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MatrixBot:
    def __init__(self):
        self.config = BotConfig
        self.client = AsyncClient(
            homeserver=self.config.HOMESERVER_URL,
            user=self.config.BOT_USERNAME,
            store_path=self.config.STORE_DIR
        )

        # Configure encryption settings - will be set after login

        # Add event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)

    async def login(self):
        """Login to the Matrix homeserver"""
        try:
            # Try to restore login from store first
            if os.path.exists(os.path.join(self.config.STORE_DIR, "next_batch")):
                logger.info("Attempting to restore login from store...")
                self.client.load_store()
                # Check if we need to login
                if not self.client.access_token:
                    response = await self.client.login(self.config.BOT_PASSWORD)
                else:
                    logger.info("Restored login from store")
                    return True
            else:
                response = await self.client.login(self.config.BOT_PASSWORD)

            if isinstance(response, LoginResponse):
                logger.info(f"Successfully logged in as {self.config.BOT_USERNAME}")
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
            # Check if already in room
            if room_id in self.client.rooms:
                logger.info(f"Already in room: {room_id}")
                return True

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
        """Send a message to a room"""
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                },
                ignore_unverified_devices=True
            )
            logger.info(f"Sent message to {room_id}: {message[:50]}...")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_formatted_message(self, room_id, message, formatted_message=None):
        """Send a formatted message to a room"""
        try:
            content = {
                "msgtype": "m.text",
                "body": message
            }

            if formatted_message:
                content["format"] = "org.matrix.custom.html"
                content["formatted_body"] = formatted_message

            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content,
                ignore_unverified_devices=True
            )
            logger.info(f"Sent formatted message to {room_id}")
        except Exception as e:
            logger.error(f"Error sending formatted message: {e}")
            # Fallback to simple message
            await self.send_message(room_id, message)

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Callback for when a message is received"""
        # Ignore messages from the bot itself
        if event.sender == self.client.user_id:
            return

        logger.info(f"Message from {event.sender} in {room.display_name}: {event.body}")

        # Simple command handling
        if event.body.startswith(self.config.COMMAND_PREFIX):
            await self.handle_command(room, event)

    async def handle_command(self, room: MatrixRoom, event: RoomMessageText):
        """Handle bot commands"""
        command = event.body.strip()
        sender_name = event.sender.split(':')[0][1:]  # Extract username

        if command == f"{self.config.COMMAND_PREFIX} help":
            help_message = f"""
🤖 **{self.config.get_bot_display_name()} Bot Help**

Available commands:
• `{self.config.COMMAND_PREFIX} help` - Show this help message
• `{self.config.COMMAND_PREFIX} ping` - Bot will respond with pong
• `{self.config.COMMAND_PREFIX} info` - Show bot information
• `{self.config.COMMAND_PREFIX} status` - Show bot status
• `{self.config.COMMAND_PREFIX} echo <message>` - Echo your message
• `{self.config.COMMAND_PREFIX} room` - Show room information
            """

            formatted_help = f"""
<strong>🤖 {self.config.get_bot_display_name()} Bot Help</strong><br/><br/>
Available commands:<br/>
• <code>{self.config.COMMAND_PREFIX} help</code> - Show this help message<br/>
• <code>{self.config.COMMAND_PREFIX} ping</code> - Bot will respond with pong<br/>
• <code>{self.config.COMMAND_PREFIX} info</code> - Show bot information<br/>
• <code>{self.config.COMMAND_PREFIX} status</code> - Show bot status<br/>
• <code>{self.config.COMMAND_PREFIX} echo &lt;message&gt;</code> - Echo your message<br/>
• <code>{self.config.COMMAND_PREFIX} room</code> - Show room information
            """

            await self.send_formatted_message(room.room_id, help_message.strip(), formatted_help.strip())

        elif command == f"{self.config.COMMAND_PREFIX} ping":
            await self.send_message(room.room_id, f"Pong! 🏓 Hello {sender_name}!")

        elif command == f"{self.config.COMMAND_PREFIX} info":
            info_message = f"""
📊 **Bot Information**
• Username: {self.config.BOT_USERNAME}
• Homeserver: {self.config.HOMESERVER_URL}
• Current Room: {room.display_name}
• Room ID: {room.room_id}
• Bot Version: 1.0.0
            """
            await self.send_message(room.room_id, info_message.strip())

        elif command == f"{self.config.COMMAND_PREFIX} status":
            room_count = len(self.client.rooms)
            await self.send_message(room.room_id, f"✅ Bot is running and healthy!\n📊 Connected to {room_count} rooms")

        elif command.startswith(f"{self.config.COMMAND_PREFIX} echo "):
            message_to_echo = command[len(f"{self.config.COMMAND_PREFIX} echo "):].strip()
            if message_to_echo:
                await self.send_message(room.room_id, f"🔊 Echo: {message_to_echo}")
            else:
                await self.send_message(room.room_id, "❌ Please provide a message to echo!")

        elif command == f"{self.config.COMMAND_PREFIX} room":
            member_count = len(room.users)
            room_info = f"""
🏠 **Room Information**
• Name: {room.display_name or 'No name set'}
• Room ID: {room.room_id}
• Members: {member_count}
• Topic: {room.topic or 'No topic set'}
• Encrypted: {'Yes' if room.encrypted else 'No'}
            """
            await self.send_message(room.room_id, room_info.strip())

        else:
            await self.send_message(room.room_id, f"❓ Unknown command. Type '{self.config.COMMAND_PREFIX} help' for available commands.")

    async def start(self):
        """Start the bot"""
        logger.info("Starting Matrix bot...")

        # Validate configuration
        if not self.config.validate():
            logger.error("Invalid configuration, exiting")
            return

        # Create store directory
        os.makedirs(self.config.STORE_DIR, exist_ok=True)

        # Login
        if not await self.login():
            logger.error("Failed to login, exiting")
            return

        # Configure encryption settings after login
        if self.client.olm:
            self.client.olm.verify_keys = False

        # Join target room
        if await self.join_room(self.config.TARGET_ROOM_ID):
            # Send greeting message after a short delay to ensure room is ready
            await asyncio.sleep(2)
            await self.send_message(self.config.TARGET_ROOM_ID, self.config.GREETING_MESSAGE)

        # Start syncing
        logger.info("Starting sync...")
        try:
            await self.client.sync_forever(timeout=self.config.SYNC_TIMEOUT)
        except Exception as e:
            logger.error(f"Sync error: {e}")
            raise

    async def close(self):
        """Close the client connection"""
        try:
            await self.client.close()
            logger.info("Bot connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

async def main():
    """Main function"""
    logger.info("Initializing Matrix Bot...")

    # Create bot instance
    bot = MatrixBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
