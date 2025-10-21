from datetime import datetime, timedelta
import uuid
import logging
from fastapi import HTTPException
from sqlalchemy import UUID, func, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Any, Dict, List, Optional
from decimal import Decimal

from app.models.user_models import Driver
from ..models.order_models import Order, OrderStatus
from ..schemas.order_schemas import OrderCreate, OrderAccept, TrackingSessionResponse
from ..schemas.user_schemas import DriverLocationResponse
from ..utils.redis_client import RedisService
from ..services.payment_service import PaymentService
from ..schemas.payment_schemas import PaymentCreate, PaymentType, PaymentMethod, RefundCreate
from ..models.payment_models import PaymentStatus, Refund
from ..services.pricing_service import PricingService

from app.models.user_models import Driver, User  # Added User import

# Configure logger for OrderService
logger = logging.getLogger(__name__)

class OrderService:
    @staticmethod
    def _calculate_price(distance_km: Decimal) -> Decimal:
        """Calculate order price based on distance with detailed logging"""
        logger.info(f"🧮 Starting price calculation for distance: {distance_km} km")

        # Get current pricing configuration from PricingService
        
        final_price = PricingService.calculate_price(distance_km)

        logger.info(f"🏁 Price calculation complete: {distance_km} km → R{final_price}")
        return final_price

    
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate, admin_custom_price: Optional[Decimal] = None) -> Order:
        """Create a new order with proper error handling and logging. Supports admin custom pricing."""
        logger.info("🆕 ===== STARTING ORDER CREATION =====")
        logger.info(f"📋 Order details - Client ID: {order_data.client_id}, Type: {order_data.order_type}")
        logger.info(f"📍 Pickup: {order_data.pickup_address} ({order_data.pickup_latitude}, {order_data.pickup_longitude})")
        logger.info(f"🎯 Dropoff: {order_data.dropoff_address} ({order_data.dropoff_latitude}, {order_data.dropoff_longitude})")
        logger.info(f"📏 Raw distance input: '{order_data.distance_km}' (type: {type(order_data.distance_km)})")
        
        try:
            # Convert distance_km from string to Decimal
            logger.debug("🔄 Converting distance to Decimal format...")
            distance_km_decimal = Decimal(str(order_data.distance_km))
            logger.info(f"✅ Distance conversion successful: {distance_km_decimal} km (Decimal)")
        except (ValueError, TypeError, Exception) as e:
            logger.error(f"❌ Distance conversion failed: {order_data.distance_km} - Error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid distance_km format: {order_data.distance_km}") from e

        # Calculate price based on distance or use admin custom price
        if admin_custom_price is not None:
            order_price = admin_custom_price
            logger.info(f"💰 Admin custom price applied: R{admin_custom_price}")
        else:
            logger.info("💵 Initiating standard price calculation...")
            order_price = OrderService._calculate_price(distance_km_decimal)
            logger.info(f"💰 Standard calculated price: R{order_price}")

        # Log optional fields if present
        if order_data.special_instructions:
            logger.info(f"📝 Special instructions: {order_data.special_instructions}")
        if order_data.patient_details:
            logger.info(f"🏥 Patient details provided: {len(str(order_data.patient_details))} characters")
        if order_data.medical_items:
            logger.info(f"💊 Medical items: {order_data.medical_items}")

        try:
            logger.info("🏗️ Creating Order object...")
            order = Order(
                client_id=order_data.client_id,
                order_type=order_data.order_type.value,
                pickup_address=order_data.pickup_address,
                pickup_latitude=order_data.pickup_latitude,
                pickup_longitude=order_data.pickup_longitude,
                dropoff_address=order_data.dropoff_address,
                dropoff_latitude=order_data.dropoff_latitude,
                dropoff_longitude=order_data.dropoff_longitude,
                special_instructions=order_data.special_instructions,
                patient_details=order_data.patient_details,
                medical_items=order_data.medical_items,
                distance_km=distance_km_decimal,
                price=order_price,
                total_paid=Decimal("0.00"),  # Explicitly initialize payment tracking fields
                total_refunded=Decimal("0.00")
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
            
        except IntegrityError as e:
            logger.error(f"❌ Database integrity error during order creation: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Order creation failed due to data integrity issue: {str(e)}") from e
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during order creation: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error during order creation: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected error during order creation: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Unexpected error during order creation: {str(e)}") from e
    
    @staticmethod
    def get_pending_orders(db: Session) -> List[Order]:
        """Fetch all pending orders"""
        logger.info("🔍 Fetching pending orders...")
        try:
            orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
            logger.info(f"📋 Found {len(orders)} pending orders")
            return orders
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching pending orders: {str(e)}")
            raise ValueError(f"Error fetching pending orders: {str(e)}") from e
    
    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept) -> Order:
        """Accept an order and assign it to a driver"""
        logger.info(f"🤝 ===== ACCEPTING ORDER {order_id} =====")
        logger.info(f"👨‍💼 Driver ID: {accept_data.driver_id}")

        try:
            # Check if the driver exists
            driver = db.query(Driver).filter(Driver.driver_id == accept_data.driver_id).first()
            if not driver:
                logger.error(f"❌ Driver not found: {accept_data.driver_id}")
                raise ValueError("Driver not found")

            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError("Order not found")

            logger.info(f"📋 Found order - Current status: {order.status.value}")

            # Validate status transition
            if order.status != OrderStatus.PENDING:
                logger.error(f"❌ Invalid order status for acceptance: {order.status.value}")
                raise ValueError("Order already accepted or completed")

            # Check if driver is already assigned to another active order
            active_orders = db.query(Order).filter(
                Order.driver_id == accept_data.driver_id,
                Order.status.in_([OrderStatus.ACCEPTED, OrderStatus.IN_TRANSIT, OrderStatus.PICKED_UP])
            ).count()

            if active_orders > 0:
                logger.error(f"❌ Driver {accept_data.driver_id} already has active orders")
                raise ValueError("Driver already has active orders")

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

            # Send push notification to client
            try:
                client_user = db.query(User).filter(User.id == order.client_id).first()
                if client_user and client_user.fcm_token:
                    from app.utils.fcm_client import send_push_notification
                    send_push_notification(
                        device_token=client_user.fcm_token,
                        title="Order Accepted!",
                        body=f"Your driver has accepted order #{order.id}. They are on their way.",
                        data={"order_id": str(order.id), "type": "ORDER_ACCEPTED"}
                    )
                    logger.info(f"📱 Push notification sent to client {order.client_id}")
                else:
                    logger.warning(f"⚠️ No FCM token found for client {order.client_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send push notification: {str(e)}")

            logger.info("🎉 ===== ORDER ACCEPTANCE COMPLETED =====")
            return order
            
        except IntegrityError as e:
            logger.error(f"❌ Database integrity error during order acceptance: {str(e)}")
            db.rollback()
            raise ValueError(f"Order acceptance failed due to data integrity issue: {str(e)}") from e
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during order acceptance: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during order acceptance: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Unexpected error during order acceptance: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        """Update the status of an order"""
        logger.info(f"🔄 Updating order status: {order_id} → {new_status.value}")

        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError("Order not found")

            old_status = order.status.value

            # Validate status transition
            valid_transitions = {
                OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
                OrderStatus.ACCEPTED: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
                OrderStatus.IN_TRANSIT: [OrderStatus.PICKED_UP, OrderStatus.CANCELLED],
                OrderStatus.PICKED_UP: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
                OrderStatus.DELIVERED: [OrderStatus.COMPLETED],
                OrderStatus.COMPLETED: [],
                OrderStatus.CANCELLED: []
            }

            current_status = order.status
            if new_status not in valid_transitions.get(current_status, []):
                logger.error(f"❌ Invalid status transition: {current_status.value} → {new_status.value}")
                raise ValueError(f"Invalid status transition from {current_status.value} to {new_status.value}")

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

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error updating order status: {str(e)}")
            db.rollback()
            raise ValueError(f"Error updating order status: {str(e)}") from e
    
    @staticmethod
    def get_client_orders(db: Session, client_id: str) -> List[Order]:
        """Get all orders for a specific client"""
        logger.info(f"🔍 Fetching orders for client: {client_id}")
        try:
            try:
                orders = db.query(Order).filter(Order.client_id == client_id).all()
                logger.info(f"📋 Found {len(orders)} orders for client {client_id}")
                return orders
            except LookupError as e:
                logger.error(f"❌ Enum decoding error fetching client orders: {str(e)}")
                # Diagnostic: inspect raw enum values in DB to validate mismatch
                try:
                    diag_rows = db.execute(
                        text(
                            "SELECT order_type::text AS order_type, COUNT(*) AS cnt "
                            "FROM orders WHERE client_id = :cid GROUP BY order_type::text"
                        ),
                        {"cid": client_id}
                    ).fetchall()
                    if diag_rows:
                        distinct_vals = ", ".join([f"{row[0]}({row[1]})" for row in diag_rows])
                    else:
                        distinct_vals = "none"
                    logger.error(f"🧪 Enum diagnostics - distinct order_type values for client {client_id}: {distinct_vals}")
                except Exception as diag_ex:
                    logger.error(f"⚠️ Enum diagnostics failed: {diag_ex}")
                # Re-raise as ValueError to keep service contract consistent
                raise ValueError("OrderType enum mismatch between DB and application. See logs for diagnostics.") from e
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching client orders: {str(e)}")
            raise ValueError(f"Error fetching client orders: {str(e)}") from e
    
    @staticmethod
    def get_driver_orders(db: Session, driver_id: str) -> List[Order]:
        """Get all orders for a specific driver"""
        logger.info(f"🔍 Fetching orders for driver: {driver_id}")
        try:
            orders = db.query(Order).filter(Order.driver_id == driver_id).all()
            logger.info(f"📋 Found {len(orders)} orders for driver {driver_id}")
            return orders
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching driver orders: {str(e)}")
            raise ValueError(f"Error fetching driver orders: {str(e)}") from e

    @staticmethod
    def get_all_orders(db: Session) -> List[Order]:
        """Get all orders in the system"""
        logger.info("🔍 Fetching all orders...")
        try:
            orders = db.query(Order).all()
            logger.info(f"📋 Found {len(orders)} total orders")
            return orders
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching all orders: {str(e)}")
            raise ValueError(f"Error fetching all orders: {str(e)}") from e

    @staticmethod
    def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
        """Get a specific order by ID"""
        logger.info(f"🔍 Fetching order by ID: {order_id}")
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                logger.info(f"✅ Order found - Status: {order.status.value}, Price: R{order.price}")
            else:
                logger.warning(f"❌ Order not found: {order_id}")
            return order
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching order by ID: {str(e)}")
            raise ValueError(f"Error fetching order: {str(e)}") from e

    @staticmethod
    def start_order_tracking(db: Session, order_id: str, client_id: str) -> TrackingSessionResponse:
        """Start tracking for an order"""
        logger.info(f"🎯 Starting tracking for order: {order_id} (Client: {client_id})")
        
        try:
            order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
            if not order:
                logger.error(f"❌ Order not found or access denied: {order_id}")
                raise ValueError("Order not found or access denied.")

            logger.info(f"📋 Order status: {order.status.value}")
            
            if order.status not in [OrderStatus.ACCEPTED, OrderStatus.IN_TRANSIT, OrderStatus.PICKED_UP]:
                logger.error(f"❌ Order status '{order.status.value}' does not allow tracking")
                raise ValueError(f"Order status '{order.status.value}' does not allow tracking.")

            # Generate tracking session ID
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
                status="active",
                message="Real-time tracking session started."
            )
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error starting order tracking: {str(e)}")
            raise ValueError(f"Error starting order tracking: {str(e)}") from e

    @staticmethod
    def delete_order(db: Session, order_id: str, client_id: Optional[str] = None, is_admin: bool = False) -> Order:
        """
        Permanently delete an order from the database.
        
        Args:
            db: Database session
            order_id: The ID of the order to delete
            client_id: The client ID (for access control, ignored if is_admin=True)
            is_admin: Whether the request is from an admin (bypasses client ownership check)
            
        Returns:
            Order: The deleted order object
            
        Raises:
            ValueError: If order not found, access denied, or deletion constraints violated
        """
        logger.info(f"🗑️ Deleting order: {order_id} (Admin: {is_admin})")
        
        try:
            # Build query based on admin status
            query = db.query(Order).filter(Order.id == order_id)
            if not is_admin and client_id:
                query = query.filter(Order.client_id == client_id)
                logger.info(f"🔒 Client-restricted deletion for: {client_id}")
            
            order = query.first()
            
            if not order:
                logger.error(f"❌ Order not found or access denied: {order_id}")
                raise ValueError("Order not found or access denied.")

            logger.info(f"📋 Order found - Status: {order.status.value}, Client: {order.client_id}")
            
            # Optional: Add business logic to prevent deletion of certain orders
            # For example, you might not want to delete completed orders for audit purposes
            non_deletable_statuses = [OrderStatus.COMPLETED, OrderStatus.DELIVERED]  # Adjust as needed
            if not is_admin and order.status in non_deletable_statuses:
                logger.error(f"❌ Order cannot be deleted - Status: {order.status.value}")
                raise ValueError(f"Order cannot be deleted. Status: {order.status.value}")

            # Store order details for logging before deletion
            order_details = {
                "id": order.id,
                "client_id": order.client_id,
                "driver_id": order.driver_id,
                "status": order.status.value,
                "price": str(order.price),
                "created_at": order.created_at
            }

            logger.info("💾 Permanently deleting order from database...")
            db.delete(order)
            db.commit()
            
            logger.info(f"✅ Order deleted successfully:")
            logger.info(f"   • Order ID: {order_details['id']}")
            logger.info(f"   • Client ID: {order_details['client_id']}")
            logger.info(f"   • Status was: {order_details['status']}")
            logger.info(f"   • Price was: R{order_details['price']}")
            
            # Clean up Redis cache if it exists
            try:
                # Check if the method exists before calling it
                if hasattr(RedisService, 'delete_order_status'):
                    RedisService.delete_order_status(order.id)
                    logger.debug("✅ Redis cache cleaned up")
                else:
                    logger.debug("⚠️ Redis cleanup method not available")
            except Exception as e:
                logger.warning(f"⚠️ Redis cleanup failed: {str(e)}")
            
            # Return the order object (note: it's now detached from the session)
            return order
            
        except IntegrityError as e:
            logger.error(f"❌ Integrity constraint violation during deletion: {str(e)}")
            db.rollback()
            raise ValueError(f"Cannot delete order due to foreign key constraints: {str(e)}") from e

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during deletion: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during deletion: {str(e)}") from e

        except Exception as e:
            logger.error(f"❌ Unexpected error during deletion: {str(e)}")
            db.rollback()
            raise ValueError(f"Unexpected error during deletion: {str(e)}") from e

    @staticmethod
    def get_order_driver_location(db: Session, order_id: str, client_id: str) -> Optional[DriverLocationResponse]:
        """Get the current location of the driver for an order"""
        logger.info(f"📍 Getting driver location for order: {order_id} (Client: {client_id})")
        
        try:
            order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
            if not order:
                logger.error(f"❌ Order not found or access denied: {order_id}")
                raise ValueError("Order not found or access denied.")
            
            # Kilo Code Debug: Log current status and driver ID to diagnose inconsistency
            logger.debug(f"🧪 Order {order_id} retrieved. Status: {order.status.value}, Driver ID: {order.driver_id}")

            # Kilo Code Debug: Expire the object to ensure we get the latest state from DB
            # This addresses the potential stale session issue.
            db.expire(order)
            
            # Accessing attributes now forces a refresh from the database
            if not order.driver_id:
                logger.warning(f"⏳ No driver assigned to order yet. Status is {order.status.value}")
                return None
                
            logger.info(f"🔍 Fetching location for driver: {order.driver_id}")
            location_data = RedisService.get_driver_location(order.driver_id)
            if not location_data:
                logger.warning(f"❌ Driver location not available in Redis for: {order.driver_id}")
                return None

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
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error getting driver location: {str(e)}")
            raise ValueError(f"Error getting driver location: {str(e)}") from e

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
        from ..models.payment_models import Payment, Refund

        if not client_id or not isinstance(client_id, str):
            logger.error(f"❌ Invalid client_id provided: {client_id}")
            raise ValueError("client_id must be a non-empty string")
        
        logger.info(f"🗑️ Starting deletion of all orders for client: {client_id}")
        
        deletion_summary = {
            "client_id": client_id,
            "orders_found": 0,
            "orders_deleted": 0,
            "payments_deleted": 0,
            "refunds_deleted": 0,
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
            
            # --- Explicitly delete related records to satisfy foreign key constraints ---
            
            # 1. Get IDs of orders to be deleted
            order_ids_to_delete = db.query(Order.id).filter(Order.client_id == client_id).subquery()

            # 2. Delete Refunds associated with these orders
            refunds_deleted = db.query(Refund).filter(Refund.order_id.in_(order_ids_to_delete)).delete(synchronize_session=False)
            deletion_summary["refunds_deleted"] = refunds_deleted
            logger.info(f"🗑️ Deleted {refunds_deleted} refunds for client {client_id}'s orders.")

            # 3. Delete Payments associated with these orders
            payments_deleted = db.query(Payment).filter(Payment.order_id.in_(order_ids_to_delete)).delete(synchronize_session=False)
            deletion_summary["payments_deleted"] = payments_deleted
            logger.info(f"🗑️ Deleted {payments_deleted} payments for client {client_id}'s orders.")

            # 4. Delete Orders
            deleted_count = db.query(Order).filter(Order.client_id == client_id).delete(synchronize_session=False)
            deletion_summary["orders_deleted"] = deleted_count
            logger.info(f"🗑️ Deleted {deleted_count} orders for client {client_id}")
            
            # Commit the transaction
            logger.info("💾 Committing deletions to database...")
            db.commit()
            
            logger.info(f"✅ Successfully deleted orders, payments, and refunds for client {client_id}")
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
        
    @staticmethod
    def admin_update_price(db: Session, order_id: str, new_price: Decimal, reason: Optional[str] = None) -> Order:
        """Admin override order price with logging and validation"""
        logger.info(f"👑 ===== ADMIN PRICE UPDATE =====")
        logger.info(f"🆔 Order ID: {order_id}")
        logger.info(f"💰 New price: R{new_price}")
        if reason:
            logger.info(f"📝 Reason: {reason}")

        try:
            # Note: Using 'id' instead of 'order_id' based on your existing code
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order with ID {order_id} not found")

            # Validate new price
            if new_price < Decimal("0"):
                logger.error(f"❌ Invalid price: R{new_price}")
                raise ValueError("Price cannot be negative")

            old_price = order.price
            order.price = new_price

            logger.info(f"💰 Admin price override - Order {order_id}: R{old_price} → R{new_price}")
            if reason:
                logger.info(f"📝 Reason: {reason}")

            db.commit()
            db.refresh(order)
            
            # Update Redis cache if needed
            try:
                RedisService.set_order_status(order.id, order.status.value)
                logger.debug("✅ Redis cache updated")
            except Exception as e:
                logger.warning(f"⚠️ Redis cache update failed: {str(e)}")

            logger.info("🎉 ===== ADMIN PRICE UPDATE COMPLETED =====")
            return order

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during admin price update: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during price update: {str(e)}") from e

    @staticmethod
    def admin_update_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        """Admin update order status with validation"""
        logger.info(f"👑 ===== ADMIN STATUS UPDATE =====")
        logger.info(f"🆔 Order ID: {order_id}")
        logger.info(f"📊 New status: {new_status.value}")

        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order with ID {order_id} not found")

            old_status = order.status
            order.status = new_status

            logger.info(f"📊 Admin status update - Order {order_id}: {old_status.value} → {new_status.value}")

            db.commit()
            db.refresh(order)
            
            # Update Redis cache
            try:
                RedisService.set_order_status(order.id, order.status.value)
                logger.debug("✅ Redis cache updated")
            except Exception as e:
                logger.warning(f"⚠️ Redis cache update failed: {str(e)}")

            logger.info("🎉 ===== ADMIN STATUS UPDATE COMPLETED =====")
            return order

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during admin status update: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during status update: {str(e)}") from e

    @staticmethod
    def search_orders(db: Session, filters: Dict[str, Any], limit: int = 50) -> List[Order]:
        """Search orders with multiple filters for admin dashboard"""
        logger.info(f"🔍 ===== ADMIN ORDER SEARCH =====")
        logger.info(f"📋 Filters: {filters}")
        logger.info(f"🔢 Limit: {limit}")

        try:
            query = db.query(Order)

            # Apply filters
            if filters.get("client_email"):
                # Join with User table to filter by email
                query = query.join(User, Order.client_id == User.id)\
                            .filter(User.email.ilike(f"%{filters['client_email']}%"))
                logger.debug(f"🔍 Filtering by client email: {filters['client_email']}")

            if filters.get("status"):
                # Convert string to OrderStatus if needed
                if isinstance(filters["status"], str):
                    try:
                        status_filter = OrderStatus(filters["status"])
                        query = query.filter(Order.status == status_filter)
                        logger.debug(f"📊 Filtering by status: {status_filter.value}")
                    except ValueError as e:
                        logger.warning(f"⚠️ Invalid status filter: {filters['status']} - {str(e)}")
                        # Skip this filter instead of failing the entire query
                else:
                    query = query.filter(Order.status == filters["status"])

            if filters.get("min_price"):
                min_price = Decimal(str(filters["min_price"]))
                query = query.filter(Order.price >= min_price)
                logger.debug(f"💰 Min price filter: R{min_price}")

            if filters.get("max_price"):
                max_price = Decimal(str(filters["max_price"]))
                query = query.filter(Order.price <= max_price)
                logger.debug(f"💰 Max price filter: R{max_price}")

            if filters.get("driver_id"):
                query = query.filter(Order.driver_id == filters["driver_id"])
                logger.debug(f"🚗 Filtering by driver: {filters['driver_id']}")

            if filters.get("date_from"):
                query = query.filter(Order.created_at >= filters["date_from"])
                logger.debug(f"📅 Date from: {filters['date_from']}")

            if filters.get("date_to"):
                query = query.filter(Order.created_at <= filters["date_to"])
                logger.debug(f"📅 Date to: {filters['date_to']}")

            # Order by most recent first
            query = query.order_by(Order.created_at.desc())

            results = query.limit(limit).all()
            logger.info(f"✅ Found {len(results)} orders matching criteria")
            return results

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during order search: {str(e)}")
            raise ValueError(f"Error searching orders: {str(e)}") from e

    @staticmethod
    def get_admin_stats(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive admin statistics"""
        logger.info(f"📊 ===== GENERATING ADMIN STATS ({days} days) =====")

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            logger.info(f"📅 Stats period: {cutoff_date.date()} to {datetime.now().date()}")

            # Total orders in period
            total_orders = db.query(Order).filter(Order.created_at >= cutoff_date).count()

            # Orders by status
            orders_by_status_query = db.query(Order.status, func.count(Order.id))\
                .filter(Order.created_at >= cutoff_date)\
                .group_by(Order.status).all()
            
            orders_by_status = {status.value: count for status, count in orders_by_status_query}

            # Revenue calculations
            revenue_query = db.query(func.sum(Order.price))\
                .filter(Order.created_at >= cutoff_date)\
                .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.DELIVERED]))\
                .scalar()
            total_revenue = revenue_query or Decimal("0")

            # Average price
            avg_price_query = db.query(func.avg(Order.price))\
                .filter(Order.created_at >= cutoff_date).scalar()
            avg_price = avg_price_query or Decimal("0")

            # Active drivers (you'll need to adjust this based on your Driver model)
            active_drivers = db.query(Driver).filter(Driver.is_available == True).count()

            # Top clients by order count
            top_clients = db.query(Order.client_id, func.count(Order.id).label('order_count'))\
                .filter(Order.created_at >= cutoff_date)\
                .group_by(Order.client_id)\
                .order_by(func.count(Order.id).desc())\
                .limit(10).all()

            # Calculate average price safely
            safe_avg_price = float(avg_price) if total_orders > 0 else 0.0

            stats = {
                "period_days": days,
                "period_start": cutoff_date.isoformat(),
                "period_end": datetime.now().isoformat(),
                "total_orders": total_orders,
                "orders_by_status": orders_by_status,
                "total_revenue": float(total_revenue),
                "average_price": safe_avg_price,
                "active_drivers": active_drivers,
                "top_clients": [{"client_id": client_id, "orders": count} for client_id, count in top_clients]
            }

            logger.info(f"📊 Stats generated successfully:")
            logger.info(f"   • Total orders: {total_orders}")
            logger.info(f"   • Total revenue: R{total_revenue}")
            logger.info(f"   • Active drivers: {active_drivers}")

            return stats

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating admin stats: {str(e)}")
            raise ValueError(f"Error generating admin stats: {str(e)}") from e

    @staticmethod
    def get_price_breakdown(db: Session, order_id: str) -> Dict[str, Any]:
        """Get detailed price breakdown analysis for an order"""
        logger.info(f"💰 ===== PRICE BREAKDOWN ANALYSIS =====")
        logger.info(f"🆔 Order ID: {order_id}")

        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {order_id}")
                raise ValueError(f"Order with ID {order_id} not found")

            # Get current pricing parameters from PricingService
            from ..services.pricing_service import PricingService
            pricing = PricingService.get_current_pricing()
            rate_per_km = pricing["rate_per_km"]
            minimum_fare = pricing["minimum_fare"]

            # Calculate what the price should be with current rates
            distance_km = order.distance_km or Decimal("0")
            # Ensure distance_km is a valid Decimal
            try:
                distance_km = Decimal(str(distance_km))
            except (ValueError, TypeError):
                distance_km = Decimal("0")
                logger.warning(f"⚠️ Invalid distance_km value: {order.distance_km}, using 0")

            calculated_price = distance_km * rate_per_km
            should_be_price = max(calculated_price, minimum_fare)

            # Determine if minimum fare was applied
            minimum_applied = calculated_price < minimum_fare

            breakdown = {
                "order_id": order_id,
                "actual_price": float(order.price),
                "distance_km": float(distance_km),
                "rate_per_km": float(rate_per_km),
                "minimum_fare": float(minimum_fare),
                "calculated_price": float(calculated_price),
                "should_be_price": float(should_be_price),
                "minimum_fare_applied": minimum_applied,
                "is_custom_price": float(order.price) != float(should_be_price),
                "difference": float(order.price - should_be_price),
                "order_status": order.status.value,
                "created_at": order.created_at.isoformat()
            }

            logger.info(f"💰 Price breakdown completed:")
            logger.info(f"   • Actual: R{order.price}")
            logger.info(f"   • Should be: R{should_be_price}")
            logger.info(f"   • Custom price: {breakdown['is_custom_price']}")
            logger.info(f"   • Difference: R{breakdown['difference']}")

            return breakdown

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating price breakdown: {str(e)}")
            raise ValueError(f"Error generating price breakdown: {str(e)}") from e

    @staticmethod
    def get_revenue_report(db: Session, days: int = 30) -> Dict[str, Any]:
        """Generate detailed revenue report for admin"""
        logger.info(f"💵 ===== REVENUE REPORT ({days} days) =====")

        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Completed orders only for revenue
            completed_orders = db.query(Order)\
                .filter(Order.created_at >= cutoff_date)\
                .filter(Order.status.in_([OrderStatus.COMPLETED, OrderStatus.DELIVERED]))\
                .all()

            total_revenue = sum(order.price for order in completed_orders)
            order_count = len(completed_orders)
            
            # Daily revenue breakdown
            daily_revenue = {}
            for order in completed_orders:
                date_key = order.created_at.date().isoformat()
                if date_key not in daily_revenue:
                    daily_revenue[date_key] = {"revenue": 0, "orders": 0}
                daily_revenue[date_key]["revenue"] += float(order.price)
                daily_revenue[date_key]["orders"] += 1

            # Average revenue per order
            avg_revenue = total_revenue / order_count if order_count > 0 else Decimal("0")

            report = {
                "period_days": days,
                "period_start": cutoff_date.date().isoformat(),
                "period_end": datetime.now().date().isoformat(),
                "total_revenue": float(total_revenue),
                "completed_orders": order_count,
                "average_revenue_per_order": float(avg_revenue),
                "daily_breakdown": daily_revenue
            }

            logger.info(f"💵 Revenue report generated:")
            logger.info(f"   • Total revenue: R{total_revenue}")
            logger.info(f"   • Completed orders: {order_count}")
            logger.info(f"   • Avg per order: R{avg_revenue}")

            return report

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating revenue report: {str(e)}")
            raise ValueError(f"Error generating revenue report: {str(e)}") from e
