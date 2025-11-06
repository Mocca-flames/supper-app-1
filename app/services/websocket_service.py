from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
import logging
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from ..utils.redis_client import RedisService
from ..database import get_db
from ..services.user_service import UserService
from ..models.user_models import Driver

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connections by order_id for order tracking
        self.order_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

            # Set driver availability to False upon disconnection
            db = next(get_db())
            driver = db.query(Driver).filter(Driver.driver_id == user_id).first()
            if driver:
                driver.is_available = False
                db.commit()
                logger.info(f"Driver {user_id} set to unavailable due to disconnection.")
            db.close()

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def send_order_update(self, order_id: str, message: dict):
        """Send update to all users tracking this order"""
        if order_id in self.order_connections:
            for user_id in self.order_connections[order_id]:
                await self.send_personal_message(json.dumps(message), user_id)

    def subscribe_to_order(self, order_id: str, user_id: str):
        """Subscribe user to order updates"""
        if order_id not in self.order_connections:
            self.order_connections[order_id] = []
        if user_id not in self.order_connections[order_id]:
            self.order_connections[order_id].append(user_id)

    def unsubscribe_from_order(self, order_id: str, user_id: str):
        """Unsubscribe user from order updates"""
        if order_id in self.order_connections:
            if user_id in self.order_connections[order_id]:
                self.order_connections[order_id].remove(user_id)

# Global connection manager instance
connection_manager = ConnectionManager()

class WebSocketService:
    @staticmethod
    def is_driver_online(driver_id: str) -> bool:
        """Check if a driver is currently online (has active WebSocket connection)"""
        return driver_id in connection_manager.active_connections

    @staticmethod
    async def broadcast_order_status_update(order_id: str, status: str, driver_location: dict = None):
        """Broadcast order status update to subscribed users"""
        message = {
            "type": "order_status_update",
            "order_id": order_id,
            "status": status,
            "timestamp": str(datetime.utcnow())
        }

        if driver_location:
            message["driver_location"] = driver_location

        await connection_manager.send_order_update(order_id, message)

    @staticmethod
    async def broadcast_driver_location(driver_id: str, latitude: float, longitude: float):
        """Broadcast driver location to relevant orders"""
        location_data = {
            "type": "driver_location_update",
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": str(datetime.utcnow())
        }

        # Store in Redis
        RedisService.set_driver_location(driver_id, latitude, longitude)

        # Send to all active orders for this driver
        # Note: You'll need to implement logic to find active orders for driver
        # For now, we'll store it in Redis and let the frontend pull it

    @staticmethod
    async def run_offline_driver_monitor(interval_minutes: int = 5):
        """Background task to monitor offline drivers and update their status"""
        while True:
            try:
                logger.info("Running offline driver monitor...")
                db = next(get_db())

                # Get all drivers
                drivers = db.query(Driver).all()

                for driver in drivers:
                    # Check if driver is offline (no recent location update)
                    last_seen = RedisService.get_driver_last_seen(driver.driver_id)
                    current_time = int(time.time())
                    is_offline = not last_seen or (current_time - int(last_seen)) >= 300

                    if is_offline:
                        # Automatically set is_available to false when offline
                        driver.is_available = False
                        db.commit()
                        logger.info(f"Driver {driver.driver_id} is offline")

                        # Here you could add logic to:
                        # - Notify clients about driver going offline
                        # - Reassign orders if necessary

                db.close()

            except Exception as e:
                logger.error(f"Error in offline driver monitor: {e}")

            # Wait for next interval
            await asyncio.sleep(interval_minutes * 60)
