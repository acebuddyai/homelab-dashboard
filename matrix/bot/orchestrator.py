#!/usr/bin/env python3
"""
Matrix Orchestrator Agent Launcher
Main entry point for the orchestrator agent in the multi-agent system
"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path

# Add the agents directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agents.orchestrator_agent import OrchestratorAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/store/orchestrator.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class OrchestratorLauncher:
    """Launcher and lifecycle manager for the orchestrator agent"""

    def __init__(self):
        self.agent = None
        self.running = False

    async def start(self):
        """Start the orchestrator agent"""
        try:
            # Validate environment variables
            required_vars = [
                "MATRIX_HOMESERVER_URL",
                "MATRIX_BOT_USERNAME",
                "MATRIX_BOT_PASSWORD"
            ]

            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False

            # Create store directory
            store_path = os.getenv("BOT_STORE_DIR", "/app/store")
            Path(store_path).mkdir(parents=True, exist_ok=True)

            logger.info("🎯 Starting Matrix Orchestrator Agent...")

            # Initialize agent
            self.agent = OrchestratorAgent(
                homeserver_url=os.getenv("MATRIX_HOMESERVER_URL"),
                username=os.getenv("MATRIX_BOT_USERNAME"),
                password=os.getenv("MATRIX_BOT_PASSWORD"),
                store_path=store_path
            )

            # Start agent
            success = await self.agent.start()
            if success:
                self.running = True
                logger.info("✅ Orchestrator Agent started successfully")
                return True
            else:
                logger.error("❌ Failed to start orchestrator agent")
                return False

        except Exception as e:
            logger.error(f"💥 Error starting orchestrator: {e}")
            return False

    async def stop(self):
        """Stop the orchestrator agent"""
        if self.agent and self.running:
            logger.info("🛑 Stopping orchestrator agent...")
            await self.agent.stop()
            self.running = False
            logger.info("👋 Orchestrator agent stopped")

    async def run(self):
        """Main run loop"""
        if not await self.start():
            return

        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Received interrupt signal")
        except Exception as e:
            logger.error(f"💥 Unexpected error in run loop: {e}")
        finally:
            await self.stop()

def setup_signal_handlers(launcher):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"📶 Received signal {signum}")
        launcher.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function"""
    logger.info("🚀 Matrix Orchestrator Agent Launcher")
    logger.info("====================================")

    launcher = OrchestratorLauncher()
    setup_signal_handlers(launcher)

    try:
        await launcher.run()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

    logger.info("✨ Orchestrator launcher exited")

if __name__ == "__main__":
    asyncio.run(main())
