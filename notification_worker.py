#!/usr/bin/env python3
"""
Background worker for handling push notifications based on driver proximity.
This script runs continuously and checks for drivers near clients every 60 seconds.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the notification worker"""
    logger.info("🚀 Starting Notification Worker Service")

    try:
        # Run the periodic proximity check
        await NotificationService.run_periodic_proximity_check(interval_seconds=60)

    except KeyboardInterrupt:
        logger.info("🛑 Notification worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error in notification worker: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())