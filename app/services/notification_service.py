import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models.order_models import Order, OrderStatus
from app.models.user_models import User
from app.utils.redis_client import RedisService
from app.utils.fcm_client import send_push_notification
from app.utils.helpers import haversine

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling push notifications based on driver proximity and order events"""

    # Distance threshold in kilometers for "driver near client" notifications
    DRIVER_NEAR_THRESHOLD_KM = 56

    @staticmethod
    def check_driver_proximity_and_notify(db: Session) -> int:
        """
        Check all active orders and send notifications when drivers are near clients.

        Returns:
            Number of notifications sent
        """
        logger.warning("⚠️ Driver proximity check is currently disabled.")
        return 0

    @staticmethod
    async def run_periodic_proximity_check(interval_seconds: int = 60):
        """
        Run periodic proximity checks in the background.

        Args:
            interval_seconds: How often to check (default: 60 seconds)
        """
        logger.info(f"🚀 Starting periodic proximity check service (interval: {interval_seconds}s)")

        logger.warning("⚠️ Periodic proximity check service is currently disabled.")
        return

    @staticmethod
    def send_order_status_notification(db: Session, order_id: str, status: OrderStatus, client_id: str) -> bool:
        """
        Send notification for order status changes.

        Args:
            db: Database session
            order_id: Order ID
            status: New order status
            client_id: Client user ID

        Returns:
            True if notification was sent successfully
        """
        logger.warning(f"⚠️ Order status notification for order {order_id} is currently disabled.")
        return False