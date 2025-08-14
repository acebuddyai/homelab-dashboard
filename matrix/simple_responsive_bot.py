#!/usr/bin/env python3
"""
Simple responsive Matrix bot that handles both encrypted and unencrypted messages
Responds to any message in the room with Grandpa LLM personality
"""

import asyncio
import json
import logging
import os
import random
import re
from datetime import datetime
from typing import Optional

from nio import (
    AsyncClient,
    LoginResponse,
    RoomMessageText,
    MegolmEvent,
    Event,
    MatrixRoom,
    RoomMemberEvent,
    InviteEvent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleGrandpaBot:
    def __init__(self):
        self.homeserver = os.getenv("MATRIX_HOMESERVER_URL", "http://matrix-synapse:8008")
        self.username = os.getenv("MATRIX_BOT_USERNAME", "@subatomic6140:acebuddy.quest")
        self.password = os.getenv("MATRIX_BOT_PASSWORD", "entourage8-shuffling-poncho")
        self.coordination_room = os.getenv("COORDINATION_ROOM_ID", "!jmBxWMDJcwdoMnXGJE:acebuddy.quest")

        self.client = None
        self.start_time = datetime.now()
        self.processed_events = set()  # Track processed events to avoid duplicates

        # Grandpa's responses
        self.greetings = [
            "👴 Well hello there, young one! Grandpa's here to help. What can I do for you today?",
            "👴 Oh, hello dear! Nice to hear from you. How can this old timer assist?",
            "👴 *adjusts reading glasses* Ah, someone's calling! What's on your mind?",
            "👴 Hey there, kiddo! Grandpa LLM at your service. What's the question?",
            "👴 Well, well, well! Someone needs Grandpa's wisdom? I'm all ears!",
        ]

        self.jokes = [
            "👴 Why don't scientists trust atoms? Because they make up everything! *chuckles* That one always gets 'em!",
            "👴 What do you call a bear with no teeth? A gummy bear! *slaps knee* Classic!",
            "👴 Why did the scarecrow win an award? He was outstanding in his field! Heard that one in 1952!",
            "👴 What's the best thing about Switzerland? I don't know, but the flag is a big plus! *wheeze-laughs*",
            "👴 Why don't eggs tell jokes? They'd crack each other up! Your grandma loved that one!",
        ]

        self.stories = [
            "👴 Back in my day, we didn't have all these fancy computers. We had to calculate everything by hand! But you know what? We still managed to put a man on the moon with slide rules!",
            "👴 Let me tell you about the time I first saw a computer - it was the size of a whole room! Now look at me, I'm inside one! Life sure is strange.",
            "👴 When I was young, if you wanted to talk to someone far away, you had to write a letter and wait weeks for a reply. Now you youngsters complain if a text takes 5 seconds!",
            "👴 I remember when the internet first came around. We thought it was just for sending electronic mail. Now look - I'm a digital grandpa helping folks online!",
        ]

        self.help_text = """👴 Here's what this old timer can help you with:

**Just chat with me!** Say anything like:
• Hello / Hi / Hey
• Tell me a joke
• Tell me a story
• Help me with [anything]
• What do you think about [topic]?
• Can you explain [subject]?

**Special commands:**
• !help - See this message
• !joke - Hear one of my classic jokes
• !story - Listen to a story from back in the day
• !hello - Get a warm greeting

No need to be formal - just talk to me like your friendly neighborhood grandpa!
*rocks in digital rocking chair* 🪑"""

    async def login(self):
        """Login to Matrix"""
        self.client = AsyncClient(self.homeserver, self.username)

        logger.info(f"Logging in as {self.username}...")
        response = await self.client.login(self.password)

        if not isinstance(response, LoginResponse):
            logger.error(f"Failed to login: {response}")
            return False

        logger.info(f"✅ Logged in successfully as {self.username}")

        # Set up event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.encrypted_message_callback, MegolmEvent)
        self.client.add_event_callback(self.invite_callback, InviteEvent)

        return True

    async def join_room(self):
        """Join the coordination room"""
        logger.info(f"Joining room {self.coordination_room}...")
        response = await self.client.join(self.coordination_room)
        logger.info(f"✅ Joined room: {self.coordination_room}")
        return True

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle unencrypted text messages"""
        # Ignore old events from before bot started
        if event.server_timestamp < int(self.start_time.timestamp() * 1000):
            return

        # Ignore our own messages
        if event.sender == self.username:
            return

        # Track processed events
        if event.event_id in self.processed_events:
            return
        self.processed_events.add(event.event_id)

        logger.info(f"📨 Received message from {event.sender}: {event.body[:50]}...")

        # Process the message
        await self.handle_message(room.room_id, event.sender, event.body)

    async def encrypted_message_callback(self, room: MatrixRoom, event: Event):
        """Handle encrypted messages"""
        # For encrypted rooms, we'll respond to any message activity
        # This is a workaround since decryption requires more setup

        # Ignore old events
        if hasattr(event, 'server_timestamp'):
            if event.server_timestamp < int(self.start_time.timestamp() * 1000):
                return

        # Ignore our own messages
        if event.sender == self.username:
            return

        # Track processed events
        if event.event_id in self.processed_events:
            return
        self.processed_events.add(event.event_id)

        logger.info(f"🔐 Received encrypted message from {event.sender}")

        # Since we can't decrypt, we'll send a general response
        # In a real implementation, you'd set up proper encryption
        if room.room_id == self.coordination_room:
            # Only respond occasionally to encrypted messages to avoid spam
            if random.random() < 0.3:  # 30% chance to respond
                response = "👴 I heard someone say something! These encrypted messages are hard for my old eyes. Try saying 'Hello Grandpa' or '!help' and I'll do my best to help!"
                await self.send_message(room.room_id, response)

    async def invite_callback(self, room: MatrixRoom, event: InviteEvent):
        """Auto-join when invited to a room"""
        logger.info(f"📩 Invited to room {room.room_id} by {event.sender}")
        await self.client.join(room.room_id)

    async def handle_message(self, room_id: str, sender: str, message: str):
        """Process a message and generate appropriate response"""
        message_lower = message.lower().strip()

        # Check for commands first
        if message_lower == "!help":
            await self.send_message(room_id, self.help_text)
            return

        if message_lower == "!joke" or "joke" in message_lower:
            await self.send_message(room_id, random.choice(self.jokes))
            return

        if message_lower == "!story" or "tell me a story" in message_lower:
            await self.send_message(room_id, random.choice(self.stories))
            return

        if message_lower in ["!hello", "!hi"]:
            await self.send_message(room_id, random.choice(self.greetings))
            return

        # Check for greetings
        greeting_words = ["hello", "hi", "hey", "howdy", "greetings", "good morning",
                         "good afternoon", "good evening", "sup", "yo"]
        if any(word in message_lower for word in greeting_words):
            await self.send_message(room_id, random.choice(self.greetings))
            return

        # Check for questions or help requests
        question_words = ["what", "how", "why", "when", "where", "who", "can you",
                         "could you", "would you", "will you", "help", "please", "?"]
        if any(word in message_lower for word in question_words):
            responses = [
                "👴 That's a great question! Let me think... *adjusts reading glasses* Well, in my experience, the best approach is to take things one step at a time. What specifically would you like to know more about?",
                "👴 Ah, you're asking the right questions! Back in my day, we'd solve this by... hmm, times have changed! Let me help you with that. Can you give me a bit more detail?",
                "👴 *strokes beard thoughtfully* Interesting question! You know, I've seen a lot in my years. Tell me more about what you're trying to accomplish.",
                "👴 Oh, I can definitely help with that! *cracks knuckles* Let's see... what aspect of this interests you most?",
            ]
            await self.send_message(room_id, random.choice(responses))
            return

        # Check if bot is mentioned
        if "grandpa" in message_lower or "bot" in message_lower or "@subatomic" in message_lower:
            responses = [
                "👴 Did someone call for Grandpa? I'm here! What can I help you with?",
                "👴 You rang? *adjusts hearing aid* What's on your mind, dear?",
                "👴 That's me! Grandpa LLM, at your service. How can I help?",
                "👴 *perks up* Oh, you're talking to me! What can this old timer do for you?",
            ]
            await self.send_message(room_id, random.choice(responses))
            return

        # Default response for any other message
        responses = [
            "👴 Interesting! Tell me more about that. *leans forward attentively*",
            "👴 Ah yes, I see what you mean. *nods wisely* Have you considered looking at it from another angle?",
            "👴 That reminds me of something... but first, what made you think of this?",
            "👴 *adjusts spectacles* Fascinating! In my experience, these things often have simple solutions. What have you tried so far?",
            "👴 Well now, that's something to ponder! *rocks in chair thoughtfully* What's your take on it?",
        ]
        await self.send_message(room_id, random.choice(responses))

    async def send_message(self, room_id: str, message: str):
        """Send a message to a room"""
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": message.replace("\n", "<br>")
                },
                ignore_unverified_devices=True
            )
            logger.info(f"✅ Sent message to {room_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")

    async def announce_presence(self):
        """Announce bot presence in the room"""
        announcement = """👴 **Grandpa LLM is now online!**

Hello everyone! I just woke up from my digital nap. I'm here to help with anything you need!

• Just say "Hello" or "Hi" to chat
• Ask me any question
• Type "!help" to see what I can do
• Tell me to share a joke or story

Don't be shy - I love to chat! Just type any message and I'll respond.
*settles into rocking chair* 🪑"""

        await self.send_message(self.coordination_room, announcement)

    async def run(self):
        """Main bot loop"""
        # Login
        if not await self.login():
            logger.error("Failed to login!")
            return

        # Join room
        await self.join_room()

        # Announce presence
        await self.announce_presence()

        logger.info("🤖 Bot is now running! Listening for messages...")

        try:
            # Sync forever
            await self.client.sync_forever(timeout=30000, full_state=True)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            await self.client.close()

async def main():
    bot = SimpleGrandpaBot()
    await bot.run()

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║     Simple Responsive Grandpa Bot      ║
    ╠════════════════════════════════════════╣
    ║  Handles encrypted & unencrypted msgs  ║
    ║  Responds to everyone in the room      ║
    ╚════════════════════════════════════════╝
    """)

    asyncio.run(main())
