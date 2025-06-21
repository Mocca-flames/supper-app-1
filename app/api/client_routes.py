from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict # Added Dict
from ..database import get_db
from ..services.order_service import OrderService
from ..schemas.order_schemas import OrderCreate, OrderResponse
from ..schemas.user_schemas import DriverLocationResponse # Added DriverLocationResponse
from ..auth.middleware import get_current_user, get_current_client # get_current_client might be used by other routes
from ..utils.redis_client import RedisService # Added RedisService

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
