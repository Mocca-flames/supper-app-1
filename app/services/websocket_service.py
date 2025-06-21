from fastapi import WebSocket
from typing import Dict, List
import json
from datetime import datetime # Added datetime import
from ..utils.redis_client import RedisService

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
