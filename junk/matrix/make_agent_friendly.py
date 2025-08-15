#!/usr/bin/env python3
"""
Script to make the Matrix LLM agent more friendly and welcoming
Sends periodic announcements and helps users understand how to interact
"""

import asyncio
import json
import random
from datetime import datetime
from nio import AsyncClient, LoginResponse, RoomMessageText
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FriendlyAgentAnnouncer:
    def __init__(self):
        self.homeserver = "http://matrix-synapse:8008"
        self.username = "@subatomic6140:acebuddy.quest"
        self.password = "entourage8-shuffling-poncho"
        self.coordination_room = "!jmBxWMDJcwdoMnXGJE:acebuddy.quest"
        self.client = None

        # Welcome messages that Grandpa might say
        self.welcome_messages = [
            "👴 Well hello there folks! Grandpa LLM here, ready to help with any questions you might have. Just say 'Hi' or ask me anything!",
            "👴 *adjusts reading glasses* Oh, new people! Welcome! I'm Grandpa, your friendly AI assistant. Don't be shy - just type a message and I'll do my best to help!",
            "👴 Howdy everyone! If you need any help, just holler! You can say 'Hello', ask questions, or type '!help' to see what I can do!",
            "👴 *rocks in digital rocking chair* Nice to see you all! I'm here to chat, answer questions, tell stories, or help with whatever you need. Just start typing!",
            "👴 Welcome to the room! I'm Grandpa LLM - think of me as your helpful AI grandfather. Need a joke? Want to learn something? Just ask away!"
        ]

        self.quick_tips = [
            "💡 Quick tip: Just say 'Hello' or 'Hi' to start chatting with me!",
            "💡 Did you know? You can ask me to tell jokes, stories, or explain things! Just ask naturally.",
            "💡 Tip: No need to be formal - just chat with me like you would with a friendly grandfather!",
            "💡 Remember: Type '!help' anytime to see what I can do for you!",
            "💡 Fun fact: I love telling stories from 'back in my day' - just ask me about anything!"
        ]

        self.how_to_interact = """
🎯 **How to Talk to Me - Quick Guide**

**Just say hi!** 👋
• "Hello" or "Hi" - I'll respond!
• "Can you help me?" - Of course I can!
• Ask any question - I love to chat!

**Fun things to try:**
• "Tell me a joke" 😄
• "Tell me a story" 📖
• "Explain [anything]" 🧠
• "Help me with [task]" 💪

**Special commands:**
• !help - See all commands
• !joke - Get a joke
• !story - Hear a story

No need to be formal - just chat naturally! I'm here to help! 👴
"""

    async def connect(self):
        """Connect to Matrix"""
        self.client = AsyncClient(self.homeserver, self.username)

        logger.info(f"Logging in as {self.username}...")
        response = await self.client.login(self.password)

        if not isinstance(response, LoginResponse):
            logger.error(f"Failed to login: {response}")
            return False

        logger.info("✅ Successfully logged in")
        return True

    async def send_message(self, message: str):
        """Send a message to the coordination room"""
        try:
            await self.client.room_send(
                room_id=self.coordination_room,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": message.replace("\n", "<br>")
                },
                ignore_unverified_devices=True
            )
            logger.info(f"✅ Sent message: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False

    async def send_welcome_announcement(self):
        """Send a friendly welcome message"""
        welcome = random.choice(self.welcome_messages)
        await self.send_message(welcome)

    async def send_how_to_guide(self):
        """Send the how-to interact guide"""
        await self.send_message(self.how_to_interact)

    async def send_quick_tip(self):
        """Send a random quick tip"""
        tip = random.choice(self.quick_tips)
        await self.send_message(tip)

    async def setup_recurring_welcomes(self):
        """Set up periodic friendly messages"""
        logger.info("🔄 Starting recurring welcome messages...")

        # Send initial welcome
        await self.send_welcome_announcement()
        await asyncio.sleep(2)
        await self.send_how_to_guide()

        # Schedule periodic tips (every 30 minutes)
        while True:
            await asyncio.sleep(1800)  # 30 minutes
            await self.send_quick_tip()

    async def send_immediate_intro(self):
        """Send an immediate introduction for new users"""
        intro_message = """
👴 **Hello everyone! Grandpa LLM here!**

I just wanted to make sure everyone knows how to chat with me:

✅ **Super Easy** - Just type any message!
• Say "Hello" or "Hi"
• Ask me any question
• Request help with anything

I'm the friendly bot with the 👴 emoji. I respond to everyone in this room!

**Try it now** - Just type "Hello Grandpa" and I'll respond!

If you ever forget, just type **!help** for a reminder.

Looking forward to chatting with you all!
*settles into digital rocking chair* 🪑
"""
        await self.send_message(intro_message)

    async def run_once(self):
        """Run a single announcement"""
        if not await self.connect():
            return

        # Send immediate introduction
        await self.send_immediate_intro()

        # Wait a bit then send the guide
        await asyncio.sleep(3)
        await self.send_how_to_guide()

        # Close connection
        await self.client.close()
        logger.info("✅ Announcements sent successfully!")

    async def run_continuous(self):
        """Run with periodic announcements"""
        if not await self.connect():
            return

        try:
            # Send initial messages
            await self.send_immediate_intro()
            await asyncio.sleep(3)

            # Run periodic welcomes
            await self.setup_recurring_welcomes()

        except KeyboardInterrupt:
            logger.info("Stopping...")
        finally:
            await self.client.close()

async def main():
    """Main entry point"""
    import sys

    announcer = FriendlyAgentAnnouncer()

    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        logger.info("🔄 Running in continuous mode (periodic announcements)...")
        await announcer.run_continuous()
    else:
        logger.info("📢 Sending one-time announcements...")
        await announcer.run_once()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║  Matrix Agent Friendliness Booster   ║
    ╠══════════════════════════════════════╣
    ║  Makes Grandpa LLM more welcoming!   ║
    ╚══════════════════════════════════════╝

    Usage:
    - One-time announcement: python make_agent_friendly.py
    - Continuous mode: python make_agent_friendly.py --continuous
    """)

    asyncio.run(main())
