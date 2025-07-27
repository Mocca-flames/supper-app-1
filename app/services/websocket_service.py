from fastapi import WebSocket
from typing import Dict, List
import json
from datetime import datetime # Added datetime import
from ..utils.redis_client import RedisService
from ..models.order_models import OrderStatus # Import OrderStatus
from ..services.order_service import OrderService # Import OrderService for getting orders by driver
from sqlalchemy.orm import Session # Import Session for database operations
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.order_listeners: Dict[str, List[str]] = {} # Maps order_id to list of user_ids listening
        self.user_orders: Dict[str, List[str]] = {} # Maps user_id to list of order_ids they are tracking

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected: {user_id}")
        # Also remove user from any order listeners
        orders_to_remove_from = self.user_orders.get(user_id, []).copy()
        for order_id in orders_to_remove_from:
            self.unsubscribe_from_order(order_id, user_id)
        if user_id in self.user_orders:
            del self.user_orders[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message)
            except RuntimeError as e:
                logger.error(f"Failed to send message to {user_id}: {e}")
                self.disconnect(user_id) # Disconnect if sending fails

    async def broadcast_to_order_listeners(self, order_id: str, message: dict):
        """Send update to all users tracking this order"""
        if order_id in self.order_listeners:
            for user_id in self.order_listeners[order_id]:
                await self.send_personal_message(json.dumps(message), user_id)

    def subscribe_to_order(self, order_id: str, user_id: str):
        """Subscribe user to order updates"""
        if order_id not in self.order_listeners:
            self.order_listeners[order_id] = []
        if user_id not in self.order_listeners[order_id]:
            self.order_listeners[order_id].append(user_id)
            logger.info(f"User {user_id} subscribed to order {order_id}")
        
        if user_id not in self.user_orders:
            self.user_orders[user_id] = []
        if order_id not in self.user_orders[user_id]:
            self.user_orders[user_id].append(order_id)

    def unsubscribe_from_order(self, order_id: str, user_id: str):
        """Unsubscribe user from order updates"""
        if order_id in self.order_listeners and user_id in self.order_listeners[order_id]:
            self.order_listeners[order_id].remove(user_id)
            logger.info(f"User {user_id} unsubscribed from order {order_id}")
            if not self.order_listeners[order_id]:
                del self.order_listeners[order_id]
        
        if user_id in self.user_orders and order_id in self.user_orders[user_id]:
            self.user_orders[user_id].remove(order_id)
            if not self.user_orders[user_id]:
                del self.user_orders[user_id]

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
        await connection_manager.broadcast_to_order_listeners(order_id, message)
        logger.info(f"Broadcasted status update for order {order_id}: {status}")

    @staticmethod
    async def broadcast_order_eta_update(order_id: str, new_eta: float, new_duration: float, new_distance: float):
        """Broadcast ETA update for an order to subscribed users."""
        message = {
            "type": "order_eta_updated",
            "order_id": order_id,
            "estimated_duration": new_duration,
            "estimated_distance": new_distance,
            "calculated_eta": new_eta,
            "timestamp": str(datetime.utcnow())
        }
        await connection_manager.broadcast_to_order_listeners(order_id, message)
        logger.info(f"Broadcasted ETA update for order {order_id}: ETA={new_eta}")

    @staticmethod
    async def broadcast_route_recalculated(order_id: str, route_geometry: str, new_eta: float, new_duration: float, new_distance: float):
        """Broadcast new route geometry and details after recalculation."""
        message = {
            "type": "route_recalculated",
            "order_id": order_id,
            "route_geometry": route_geometry,
            "estimated_duration": new_duration,
            "estimated_distance": new_distance,
            "calculated_eta": new_eta,
            "timestamp": str(datetime.utcnow())
        }
        await connection_manager.broadcast_to_order_listeners(order_id, message)
        logger.info(f"Broadcasted route recalculation for order {order_id}")

    @staticmethod
    async def broadcast_geocoding_completed(order_id: str, address_type: str, coordinates: dict, place_name: str):
        """Broadcast geocoding completion for an order's address."""
        message = {
            "type": "geocoding_completed",
            "order_id": order_id,
            "address_type": address_type, # e.g., "pickup", "dropoff"
            "coordinates": coordinates,
            "place_name": place_name,
            "timestamp": str(datetime.utcnow())
        }
        await connection_manager.broadcast_to_order_listeners(order_id, message)
        logger.info(f"Broadcasted geocoding completion for order {order_id}, type {address_type}")

    @staticmethod
    async def broadcast_location_validated(order_id: str, location_type: str, is_valid: bool, message_text: str):
        """Broadcast location validation status for an order's pickup/dropoff."""
        message = {
            "type": "location_validated",
            "order_id": order_id,
            "location_type": location_type, # e.g., "pickup", "dropoff"
            "is_valid": is_valid,
            "message": message_text,
            "timestamp": str(datetime.utcnow())
        }
        await connection_manager.broadcast_to_order_listeners(order_id, message)
        logger.info(f"Broadcasted location validation for order {order_id}, type {location_type}: {is_valid}")

    @staticmethod
    async def broadcast_driver_location(db: Session, driver_id: str, latitude: float, longitude: float):
        """
        Broadcast driver location to all clients tracking orders assigned to this driver.
        Requires a database session to fetch orders.
        """
        location_data = {
            "type": "driver_location_update",
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": str(datetime.utcnow())
        }
        
        # Store in Redis
        RedisService.set_driver_location(driver_id, latitude, longitude)
        logger.debug(f"Driver {driver_id} location updated in Redis: {latitude}, {longitude}")

        # Find all active orders assigned to this driver
        # This requires querying the database
        try:
            # Assuming OrderService has a method to get orders by driver_id and status
            # Only broadcast for orders that are in a trackable status
            trackable_statuses = [OrderStatus.ACCEPTED, OrderStatus.IN_TRANSIT, OrderStatus.PICKED_UP]
            driver_orders = OrderService.get_driver_orders_by_status(db, driver_id, trackable_statuses)
            
            for order in driver_orders:
                # Send the driver's location to all users subscribed to this specific order
                await connection_manager.broadcast_to_order_listeners(order.id, location_data)
                logger.debug(f"Broadcasted driver {driver_id} location to listeners of order {order.id}")
        except Exception as e:
            logger.error(f"Error broadcasting driver location for {driver_id}: {e}")
