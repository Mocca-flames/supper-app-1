from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict # Added Dict
from ..database import get_db
from ..services.order_service import OrderService
from ..services.user_service import UserService # Added UserService
from ..schemas.order_schemas import OrderCreate, OrderResponse, OrderUpdate
from ..schemas.user_schemas import DriverLocationResponse, ClientProfileUpdate, ClientResponse # Added ClientProfileUpdate, ClientResponse
from ..auth.middleware import get_current_user, get_current_client # get_current_client might be used by other routes
from ..utils.redis_client import RedisService # Added RedisService
from ..models.order_models import Order
from ..models.payment_models import PaymentStatus

router = APIRouter(prefix="/client", tags=["Client"])

@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create a new order/ride request"""
    order_data.client_id = current_user.id  # Use current_user.id (Firebase UID)
    order = OrderService.create_order(db, order_data)
    return order

@router.get("/orders", response_model=List[OrderResponse])
def get_my_orders(
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get all orders for current client"""
    orders = OrderService.get_client_orders(db, current_user.id)
    return orders

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific order details"""
    orders = OrderService.get_client_orders(db, current_user.id)
    order = next((o for o in orders if o.id == order_id), None)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    order_data: OrderUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order information (payment status, special instructions, etc.)"""
    try:
        # Verify the order belongs to the current user
        order = db.query(Order).filter(Order.id == order_id, Order.client_id == current_user.id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or access denied")

        # Update only the allowed fields
        if order_data.payment_status is not None:
            order.payment_status = order_data.payment_status

        if order_data.special_instructions is not None:
            order.special_instructions = order_data.special_instructions

        db.commit()
        db.refresh(order)

        return order

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

@router.get("/driver/{driver_id}/location", response_model=DriverLocationResponse)
def get_driver_location_route( # Renamed to avoid conflict if a similar schema exists
    driver_id: str,
    current_user = Depends(get_current_user) # Ensure user is authenticated
):
    """Get a specific driver's last known location."""
    location = RedisService.get_driver_location(driver_id)
    if not location:
        raise HTTPException(status_code=404, detail="Driver location not found or driver ID is invalid.")
    # Ensure latitude and longitude are floats
    try:
        return DriverLocationResponse(
            driver_id=driver_id,
            latitude=float(location.get("lat", 0.0)), # Provide default if key missing, though hgetall returns strings
            longitude=float(location.get("lng", 0.0))
        )
    except (ValueError, TypeError): # Catch potential conversion errors
        raise HTTPException(status_code=500, detail="Error processing location data.")

@router.put("/profile", response_model=ClientResponse)
def update_client_profile_route(
    client_data: ClientProfileUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current client's profile information."""
    if current_user.role != "client":
        raise HTTPException(status_code=403, detail="User is not a client")
    
    if not current_user.client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found for this user. Please create one first.")

    try:
        updated_client = UserService.update_client_profile(db, current_user.id, client_data)
        # To return ClientResponse, we need to ensure the 'user' field is populated.
        # The update_client_profile service method returns a Client object.
        # We can refresh the current_user object to get the updated client_profile with its user relationship loaded.
        db.refresh(current_user) # Refresh the user object to get updated relationships
        return ClientResponse(
            client_id=updated_client.client_id,
            home_address=updated_client.home_address,
            is_verified=updated_client.is_verified,
            user=current_user # Pass the refreshed current_user which now has the updated client_profile
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during client profile update: {e}")
