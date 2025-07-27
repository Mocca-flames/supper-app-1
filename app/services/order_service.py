import uuid # Added for generating session_id
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from ..models.order_models import Order, OrderStatus
from ..schemas.order_schemas import OrderCreate, OrderAccept, TrackingSessionResponse
from ..schemas.user_schemas import DriverLocationResponse
from ..utils.redis_client import RedisService
from ..services.mapbox_service import MapboxService # Import MapboxService
from ..services.location_service import LocationService # Import LocationService (will create this next)

class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        # Validate addresses using geocoding before creating the order
        pickup_coords = LocationService.geocode_address(order_data.pickup_address)
        dropoff_coords = LocationService.geocode_address(order_data.dropoff_address)

        if not pickup_coords or not dropoff_coords:
            raise ValueError("Invalid pickup or dropoff address provided.")

        order = Order(
            client_id=order_data.client_id,
            order_type=order_data.order_type,
            pickup_address=order_data.pickup_address,
            pickup_latitude=pickup_coords['latitude'],
            pickup_longitude=pickup_coords['longitude'],
            dropoff_address=order_data.dropoff_address,
            dropoff_latitude=dropoff_coords['latitude'],
            dropoff_longitude=dropoff_coords['longitude'],
            special_instructions=order_data.special_instructions,
            patient_details=order_data.patient_details,
            medical_items=order_data.medical_items
        )
        
        # Calculate route details and update order
        order = OrderService._calculate_order_details(order)

        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Cache order status in Redis
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def _calculate_order_details(order: Order) -> Order:
        # Use MapboxService to get route information
        route_info = MapboxService.get_directions(
            (order.pickup_longitude, order.pickup_latitude),
            (order.dropoff_longitude, order.dropoff_latitude)
        )

        if route_info:
            order.route_geometry = route_info.get('geometry')
            order.estimated_duration = route_info.get('duration')
            order.estimated_distance = route_info.get('distance')
            order.calculated_eta = route_info.get('eta') # Assuming ETA is part of route_info
            order.route_calculation_timestamp = route_info.get('timestamp') # Assuming timestamp is part of route_info
            # Implement distance-based pricing calculation
            # For now, a simple placeholder: $1 per km
            order.price = Decimal(order.estimated_distance / 1000 * 1.00) # distance is in meters, convert to km
        else:
            # Handle cases where route calculation fails
            order.route_geometry = None
            order.estimated_duration = None
            order.estimated_distance = None
            order.calculated_eta = None
            order.route_calculation_timestamp = None
            order.price = Decimal(0.00) # Default price if route cannot be calculated

        return order

    @staticmethod
    def get_pending_orders(db: Session) -> List[Order]:
        return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
    
    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError("Order already accepted or completed")
        
        order.driver_id = accept_data.driver_id
        order.status = OrderStatus.ACCEPTED
        order.price = accept_data.estimated_price
        
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        order.status = new_status
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def get_client_orders(db: Session, client_id: str) -> List[Order]:
        return db.query(Order).filter(Order.client_id == client_id).all()
    
    @staticmethod
    def get_driver_orders(db: Session, driver_id: str) -> List[Order]:
        return db.query(Order).filter(Order.driver_id == driver_id).all()

    @staticmethod
    def get_all_orders(db: Session) -> List[Order]:
        return db.query(Order).all()

    @staticmethod
    def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def start_order_tracking(db: Session, order_id: str, client_id: str) -> TrackingSessionResponse:
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
        if not order:
            raise ValueError("Order not found or access denied.")

        if order.status not in [OrderStatus.ACCEPTED, OrderStatus.IN_TRANSIT, OrderStatus.PICKED_UP]:
            # Depending on business logic, other statuses might also be untrackable
            raise ValueError(f"Order status '{order.status.value}' does not allow tracking.")

        # Placeholder for actual tracking session initiation
        session_id = str(uuid.uuid4())
        # Potentially store session_id and order_id mapping in Redis or another store
        
        # Check if driver is assigned for more detailed status
        if not order.driver_id:
            return TrackingSessionResponse(
                session_id=session_id,
                order_id=order_id,
                status="pending_driver_assignment",
                message="Tracking initiated, waiting for driver assignment."
            )

        return TrackingSessionResponse(
            session_id=session_id,
            order_id=order_id,
            status="active", # Or more specific based on order.status
            message="Real-time tracking session started."
        )

    @staticmethod
    def cancel_order(db: Session, order_id: str, client_id: Optional[str] = None, is_admin: bool = False) -> Order:
        query = db.query(Order).filter(Order.id == order_id)
        if not is_admin and client_id:
            query = query.filter(Order.client_id == client_id)
        
        order = query.first()
        
        if not order:
            raise ValueError("Order not found or access denied.")

        # Define cancellable statuses
        cancellable_statuses = [OrderStatus.PENDING, OrderStatus.ACCEPTED] # Add more as per business rules
        if order.status not in cancellable_statuses:
            raise ValueError(f"Order cannot be cancelled. Current status: {order.status.value}")

        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order

    @staticmethod
    def get_order_driver_location(db: Session, order_id: str, client_id: str) -> Optional[DriverLocationResponse]:
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == client_id).first()
        if not order:
            raise ValueError("Order not found or access denied.")
        
        if not order.driver_id:
            # Order might not have a driver assigned yet (e.g. PENDING status)
            return None 
            
        location_data = RedisService.get_driver_location(order.driver_id)
        if not location_data:
            return None # Driver location not available in Redis

        try:
            return DriverLocationResponse(
                driver_id=order.driver_id,
                latitude=float(location_data.get("lat", 0.0)),
                longitude=float(location_data.get("lng", 0.0))
            )
        except (ValueError, TypeError):
            # Log error or handle appropriately
            return None
