"""
Configuration file for Matrix Bot
"""

import os
from typing import Optional

class BotConfig:
    """Bot configuration class"""

    # Matrix server configuration
    HOMESERVER_URL: str = os.getenv("MATRIX_HOMESERVER_URL")
    BOT_USERNAME: str = os.getenv("MATRIX_BOT_USERNAME")
    BOT_PASSWORD: str = os.getenv("MATRIX_BOT_PASSWORD")

    # Room configuration
    TARGET_ROOM_ID: str = os.getenv("MATRIX_TARGET_ROOM_ID")

    # Bot behavior configuration
    COMMAND_PREFIX: str = os.getenv("BOT_COMMAND_PREFIX", "!bot")
    GREETING_MESSAGE: str = os.getenv("BOT_GREETING_MESSAGE",
                                    "Hello! I'm your friendly Matrix bot. Type '!bot help' to see what I can do! 🤖")

    # Sync configuration
    SYNC_TIMEOUT: int = int(os.getenv("MATRIX_SYNC_TIMEOUT", "30000"))

    # Logging configuration
    LOG_LEVEL: str = os.getenv("BOT_LOG_LEVEL", "INFO")

    # Store directory for bot data
    STORE_DIR: str = os.getenv("BOT_STORE_DIR", "/app/store")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_fields = [
            cls.HOMESERVER_URL,
            cls.BOT_USERNAME,
            cls.BOT_PASSWORD,
            cls.TARGET_ROOM_ID
        ]

        for field in required_fields:
            if not field or field.strip() == "":
                return False

        return True

    @classmethod
    def get_bot_display_name(cls) -> str:
        """Extract display name from username"""
        if cls.BOT_USERNAME.startswith("@"):
            return cls.BOT_USERNAME[1:].split(":")[0]
        return cls.BOT_USERNAME.split(":")[0]
