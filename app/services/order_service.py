import uuid # Added for generating session_id
import logging
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from typing import List, Optional # Added Optional
from decimal import Decimal
from ..models.order_models import Order, OrderStatus
from ..schemas.order_schemas import OrderCreate, OrderAccept, TrackingSessionResponse # Added TrackingSessionResponse
from ..schemas.user_schemas import DriverLocationResponse # Added DriverLocationResponse
from ..utils.redis_client import RedisService
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Configure logger for OrderService
logger = logging.getLogger(__name__)

class OrderService:
    @staticmethod
    def _calculate_price(distance_km: Decimal) -> Decimal:
        """Calculate order price based on distance with detailed logging"""
        logger.info(f"🧮 Starting price calculation for distance: {distance_km} km")
        
        # Simple pricing logic: R10 per km, with a minimum fare of R50
        # This can be scaled later with more complex logic (e.g., time of day, vehicle type)
        rate_per_km = Decimal("10.00")
        minimum_fare = Decimal("50.00")
        
        logger.debug(f"💰 Pricing parameters - Rate per km: R{rate_per_km}, Minimum fare: R{minimum_fare}")
        
        calculated_price = distance_km * rate_per_km
        final_price = max(calculated_price, minimum_fare)
        
        if calculated_price < minimum_fare:
            logger.info(f"⬆️ Applied minimum fare - Calculated: R{calculated_price}, Final: R{final_price}")
        else:
            logger.info(f"✅ Standard rate applied - Final price: R{final_price}")
            
        logger.info(f"🏁 Price calculation complete: {distance_km} km → R{final_price}")
        return final_price

    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        logger.info("🆕 ===== STARTING ORDER CREATION =====")
        logger.info(f"📋 Order details - Client ID: {order_data.client_id}, Type: {order_data.order_type}")
        logger.info(f"📍 Pickup: {order_data.pickup_address} ({order_data.pickup_latitude}, {order_data.pickup_longitude})")
        logger.info(f"🎯 Dropoff: {order_data.dropoff_address} ({order_data.dropoff_latitude}, {order_data.dropoff_longitude})")
        logger.info(f"📏 Raw distance input: '{order_data.distance_km}' (type: {type(order_data.distance_km)})")
        
        # Convert distance_km from string to Decimal
        try:
            logger.debug("🔄 Converting distance to Decimal format...")
            distance_km_decimal = Decimal(order_data.distance_km)
            logger.info(f"✅ Distance conversion successful: {distance_km_decimal} km (Decimal)")
        except Exception as e:
            logger.error(f"❌ Distance conversion failed: {order_data.distance_km} - Error: {str(e)}")
            raise ValueError(f"Invalid distance_km format: {order_data.distance_km}") from e

        # Calculate price based on distance
        logger.info("💵 Initiating price calculation...")
        order_price = OrderService._calculate_price(distance_km_decimal)
        logger.info(f"💰 Final calculated price: R{order_price}")

        # Log optional fields if present
        if order_data.special_instructions:
            logger.info(f"📝 Special instructions: {order_data.special_instructions}")
        if order_data.patient_details:
            logger.info(f"🏥 Patient details provided: {len(str(order_data.patient_details))} characters")
        if order_data.medical_items:
            logger.info(f"💊 Medical items: {order_data.medical_items}")

        logger.info("🏗️ Creating Order object...")
        order = Order(
            client_id=order_data.client_id,
            order_type=order_data.order_type,
            pickup_address=order_data.pickup_address,
            pickup_latitude=order_data.pickup_latitude,
            pickup_longitude=order_data.pickup_longitude,
            dropoff_address=order_data.dropoff_address,
            dropoff_latitude=order_data.dropoff_latitude,
            dropoff_longitude=order_data.dropoff_longitude,
            special_instructions=order_data.special_instructions,
            patient_details=order_data.patient_details,
            medical_items=order_data.medical_items,
            distance_km=distance_km_decimal, # Assign distance to the order model
            price=order_price # Assign calculated price to the order model
        )
        
        logger.info("💾 Saving order to database...")
        db.add(order)
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ Order saved successfully - Order ID: {order.id}")
        logger.info(f"📊 Order Summary:")
        logger.info(f"   • ID: {order.id}")
        logger.info(f"   • Distance: {order.distance_km} km")
        logger.info(f"   • Price: R{order.price}")
        logger.info(f"   • Status: {order.status.value}")
        logger.info(f"   • Created: {order.created_at}")
        
        # Cache order status in Redis
        logger.debug(f"🔄 Caching order status in Redis: {order.id} → {order.status.value}")
        try:
            RedisService.set_order_status(order.id, order.status.value)
            logger.debug("✅ Redis cache updated successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cache order status in Redis: {str(e)}")
        
        logger.info("🎉 ===== ORDER CREATION COMPLETED =====")
        return order
    
    @staticmethod
    def get_pending_orders(db: Session) -> List[Order]:
        logger.info("🔍 Fetching pending orders...")
        orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
        logger.info(f"📋 Found {len(orders)} pending orders")
        return orders
    
    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept) -> Order:
        logger.info(f"🤝 ===== ACCEPTING ORDER {order_id} =====")
        logger.info(f"👨‍💼 Driver ID: {accept_data.driver_id}")

        # Check if the driver exists
        driver = db.query(Driver).filter(Driver.id == accept_data.driver_id).first()
        if not driver:
            logger.error(f"❌ Driver not found: {accept_data.driver_id}")
            raise ValueError("Driver not found")

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"❌ Order not found: {order_id}")
            raise ValueError("Order not found")

        logger.info(f"📋 Found order - Current status: {order.status.value}")

        if order.status != OrderStatus.PENDING:
            logger.error(f"❌ Invalid order status for acceptance: {order.status.value}")
            raise ValueError("Order already accepted or completed")

        logger.info(f"💰 Order price: R{order.price} (calculated during creation)")

        order.driver_id = accept_data.driver_id
        order.status = OrderStatus.ACCEPTED

        logger.info("💾 Updating order in database...")
        db.commit()
        db.refresh(order)

        logger.info(f"✅ Order accepted successfully:")
        logger.info(f"   • Order ID: {order.id}")
        logger.info(f"   • Driver ID: {order.driver_id}")
        logger.info(f"   • Status: {order.status.value}")
        logger.info(f"   • Price: R{order.price}")

        # Update Redis cache
        try:
            RedisService.set_order_status(order.id, order.status.value)
            logger.debug("✅ Redis cache updated")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache update failed: {str(e)}")

        logger.info("🎉 ===== ORDER ACCEPTANCE COMPLETED =====")
        return order
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"❌ Order not found: {order_id}")
            raise ValueError("Order not found")
        
        logger.info(f"📋 Found order - Current status: {order.status.value}")
        
        if order.status != OrderStatus.PENDING:
            logger.error(f"❌ Invalid order status for acceptance: {order.status.value}")
            raise ValueError("Order already accepted or completed")
        
        logger.info(f"💰 Order price: R{order.price} (calculated during creation)")
        
        order.driver_id = accept_data.driver_id
        order.status = OrderStatus.ACCEPTED
        
        logger.info("💾 Updating order in database...")
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ Order accepted successfully:")
        logger.info(f"   • Order ID: {order.id}")
        logger.info(f"   • Driver ID: {order.driver_id}")
        logger.info(f"   • Status: {order.status.value}")
        logger.info(f"   • Price: R{order.price}")
        
        # Update Redis cache
        try:
            RedisService.set_order_status(order.id, order.status.value)
            logger.debug("✅ Redis cache updated")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache update failed: {str(e)}")
        
        logger.info("🎉 ===== ORDER ACCEPTANCE COMPLETED =====")
        return order
    
    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        logger.info(f"🔄 Updating order status: {order_id} → {new_status.value}")
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"❌ Order not found: {order_id}")
            raise ValueError("Order not found")
        
        old_status = order.status.value
        order.status = new_status
        
        logger.info("💾 Saving status update to database...")
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ Status updated: {old_status} → {new_status.value}")
        
        # Update Redis cache
        try:
            RedisService.set_order_status(order.id, order.status.value)
            logger.debug("✅ Redis cache updated")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache update failed: {str(e)}")
        
        return order
    
    @staticmethod
    def get_client_orders(db: Session, client_id: str) -> List[Order]:
        logger.info(f"🔍 Fetching orders for client: {client_id}")
        orders = db.query(Order).filter(Order.client_id == client_id).all()
        logger.info(f"📋 Found {len(orders)} orders for client {client_id}")
        return orders
    
    @staticmethod
    def get_driver_orders(db: Session, driver_id: str) -> List[Order]:
        logger.info(f"🔍 Fetching orders for driver: {driver_id}")
        orders = db.query(Order).filter(Order.driver_id == driver_id).all()
        logger.info(f"📋 Found {len(orders)} orders for driver {driver_id}")
        return orders

    @staticmethod
    def get_all_orders(db: Session) -> List[Order]:
        logger.info("🔍 Fetching all orders...")
        orders = db.query(Order).all()
        logger.info(f"📋 Found {len(orders)} total orders")
        return orders

    @staticmethod
    def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
        logger.info(f"🔍 Fetching order by ID: {order_id}")
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            logger.info(f"✅ Order found - Status: {order.status.value}, Price: R{order.price}")
        else:
            logger.warning(f"❌ Order not found: {order_id}")
        return order

    @staticmethod
    def start_order_tracking(db: Session, order_id: str, client_id: str) -> TrackingSessionResponse:
        logger.info(f"🎯 Starting tracking for order: {order_id} (Client: {client_id})")
        
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
        if not order:
            logger.error(f"❌ Order not found or access denied: {order_id}")
            raise ValueError("Order not found or access denied.")

        logger.info(f"📋 Order status: {order.status.value}")
        
        if order.status not in [OrderStatus.ACCEPTED, OrderStatus.IN_TRANSIT, OrderStatus.PICKED_UP]:
            logger.error(f"❌ Order status '{order.status.value}' does not allow tracking")
            raise ValueError(f"Order status '{order.status.value}' does not allow tracking.")

        # Placeholder for actual tracking session initiation
        session_id = str(uuid.uuid4())
        logger.info(f"🆔 Generated tracking session ID: {session_id}")
        
        # Check if driver is assigned for more detailed status
        if not order.driver_id:
            logger.warning("⏳ No driver assigned yet - tracking in pending state")
            return TrackingSessionResponse(
                session_id=session_id,
                order_id=order_id,
                status="pending_driver_assignment",
                message="Tracking initiated, waiting for driver assignment."
            )

        logger.info(f"✅ Active tracking session started for driver: {order.driver_id}")
        return TrackingSessionResponse(
            session_id=session_id,
            order_id=order_id,
            status="active", # Or more specific based on order.status
            message="Real-time tracking session started."
        )

    @staticmethod
    def cancel_order(db: Session, order_id: str, client_id: Optional[str] = None, is_admin: bool = False) -> Order:
        logger.info(f"🚫 Cancelling order: {order_id} (Admin: {is_admin})")
        
        query = db.query(Order).filter(Order.id == order_id)
        if not is_admin and client_id:
            query = query.filter(Order.client_id == client_id)
            logger.info(f"🔒 Client-restricted cancellation for: {client_id}")
        
        order = query.first()
        
        if not order:
            logger.error(f"❌ Order not found or access denied: {order_id}")
            raise ValueError("Order not found or access denied.")

        logger.info(f"📋 Current order status: {order.status.value}")
        
        # Define cancellable statuses
        cancellable_statuses = [OrderStatus.PENDING, OrderStatus.ACCEPTED] # Add more as per business rules
        if order.status not in cancellable_statuses:
            logger.error(f"❌ Order cannot be cancelled - Status: {order.status.value}")
            raise ValueError(f"Order cannot be cancelled. Current status: {order.status.value}")

        logger.info("💾 Setting order status to CANCELLED...")
        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)
        
        logger.info(f"✅ Order cancelled successfully: {order_id}")
        
        # Update Redis cache
        try:
            RedisService.set_order_status(order.id, order.status.value)
            logger.debug("✅ Redis cache updated")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache update failed: {str(e)}")
        
        return order

    @staticmethod
    def get_order_driver_location(db: Session, order_id: str, client_id: str) -> Optional[DriverLocationResponse]:
        logger.info(f"📍 Getting driver location for order: {order_id} (Client: {client_id})")
        
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
        if not order:
            logger.error(f"❌ Order not found or access denied: {order_id}")
            raise ValueError("Order not found or access denied.")
        
        if not order.driver_id:
            logger.warning("⏳ No driver assigned to order yet")
            return None 
            
        logger.info(f"🔍 Fetching location for driver: {order.driver_id}")
        location_data = RedisService.get_driver_location(order.driver_id)
        if not location_data:
            logger.warning(f"❌ Driver location not available in Redis for: {order.driver_id}")
            return None # Driver location not available in Redis

        try:
            latitude = float(location_data.get("lat", 0.0))
            longitude = float(location_data.get("lng", 0.0))
            
            logger.info(f"📍 Driver location found: ({latitude}, {longitude})")
            
            return DriverLocationResponse(
                driver_id=order.driver_id,
                latitude=latitude,
                longitude=longitude
            )
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Error parsing location data: {str(e)}")
            return None


    @staticmethod
    def delete_all_orders_for_user(db: Session, client_id: str) -> dict:
        """
        Delete all orders for a specific user with robust error handling.
        
        Args:
            db: Database session
            client_id: The client ID whose orders should be deleted
            
        Returns:
            dict: Summary of the deletion operation
            
        Raises:
            ValueError: If client_id is invalid or deletion fails
        """
        if not client_id or not isinstance(client_id, str):
            logger.error(f"❌ Invalid client_id provided: {client_id}")
            raise ValueError("client_id must be a non-empty string")
        
        logger.info(f"🗑️ Starting deletion of all orders for client: {client_id}")
        
        deletion_summary = {
            "client_id": client_id,
            "orders_found": 0,
            "orders_deleted": 0,
            "success": False,
            "error": None
        }
        
        try:
            # First, count the orders to be deleted
            order_count = db.query(Order).filter(Order.client_id == client_id).count()
            deletion_summary["orders_found"] = order_count
            
            logger.info(f"📋 Found {order_count} orders for client {client_id}")
            
            if order_count == 0:
                logger.info(f"ℹ️ No orders found for client {client_id}")
                deletion_summary["success"] = True
                return deletion_summary
            
            # Bulk delete (most efficient for large datasets)
            deleted_count = db.query(Order).filter(Order.client_id == client_id).delete()
            
            logger.info(f"🗑️ Bulk deleted {deleted_count} orders")
            deletion_summary["orders_deleted"] = deleted_count
            
            # Commit the transaction
            logger.info("💾 Committing deletions to database...")
            db.commit()
            
            logger.info(f"✅ Successfully deleted {deleted_count} orders for client {client_id}")
            deletion_summary["success"] = True
            
            return deletion_summary
            
        except IntegrityError as e:
            logger.error(f"❌ Integrity constraint violation during deletion for client {client_id}: {str(e)}")
            db.rollback()
            deletion_summary["error"] = f"Integrity constraint violation: {str(e)}"
            raise ValueError(f"Cannot delete orders due to foreign key constraints: {str(e)}") from e

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during deletion for client {client_id}: {str(e)}")
            db.rollback()
            deletion_summary["error"] = f"Database error: {str(e)}"
            raise ValueError(f"Database error during deletion: {str(e)}") from e

        except Exception as e:
            logger.error(f"❌ Unexpected error during deletion for client {client_id}: {str(e)}")
            db.rollback()
            deletion_summary["error"] = f"Unexpected error: {str(e)}"
            raise ValueError(f"Unexpected error during deletion: {str(e)}") from e
