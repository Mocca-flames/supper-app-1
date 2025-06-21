from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.order_service import OrderService
from ..services.driver_service import DriverService # Added DriverService
from ..schemas.order_schemas import OrderResponse, OrderAccept, OrderStatusUpdate
from ..schemas.user_schemas import DriverLocationUpdate, DriverProfileUpdate, DriverResponse as DriverProfileResponse, DriverAvailabilityUpdate # Added schemas
# Removed get_approved_driver, using get_current_user instead
from ..auth.middleware import get_current_user # Changed from get_current_driver
from ..models.user_models import User # Added User model for type hinting and role check
from ..utils.redis_client import RedisService

router = APIRouter(prefix="/driver", tags=["Driver"])

@router.get("/available-orders", response_model=List[OrderResponse])
def get_available_orders(
    current_user: User = Depends(get_current_user), # Changed to get_current_user
    db: Session = Depends(get_db)
):
    """Get all pending orders for drivers"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")
    orders = OrderService.get_pending_orders(db)
    return orders

@router.post("/accept-order/{order_id}", response_model=OrderResponse)
def accept_order(
    order_id: str,
    accept_data: OrderAccept,
    current_user: User = Depends(get_current_user), # Changed to get_current_user
    db: Session = Depends(get_db)
):
    """Accept an order"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")
    # Ensure driver is accepting for themselves
    if accept_data.driver_id != current_user.id: # Changed to current_user.id
        raise HTTPException(status_code=403, detail="Cannot accept order for another driver")
    
    order = OrderService.accept_order(db, order_id, accept_data)
    return order

@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    current_user: User = Depends(get_current_user), # Changed to get_current_user
    db: Session = Depends(get_db)
):
    """Get all orders for current driver"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")
    orders = OrderService.get_driver_orders(db, current_user.id) # Changed to current_user.id
    return orders

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user), # Changed to get_current_user
    db: Session = Depends(get_db)
):
    """Update order status"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")
    
    order = OrderService.update_order_status(db, order_id, status_data.status)
    
    # Verify driver owns this order
    if order.driver_id != current_user.id: # Changed to current_user.id
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    
    return order

@router.post("/location")
def update_location(
    location_data: DriverLocationUpdate,
    current_user: User = Depends(get_current_user) # Changed to get_current_user
):
    """Update driver location"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")
    RedisService.set_driver_location(
        current_user.id, # Changed to current_user.id
        location_data.latitude,
        location_data.longitude
    )
    return {"message": "Location updated successfully"}

@router.put("/profile", response_model=DriverProfileResponse)
def update_driver_profile_route(
    profile_data: DriverProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current driver's profile"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")

    updated_user = DriverService.update_driver_profile(db, current_user.id, profile_data)

    if not updated_user or not updated_user.driver_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found or update failed")

    # Construct the DriverResponse
    # Ensure all fields for DriverResponse are correctly mapped from updated_user and its driver_profile
    return DriverProfileResponse(
        driver_id=updated_user.driver_profile.driver_id,
        license_no=updated_user.driver_profile.license_no,
        vehicle_type=updated_user.driver_profile.vehicle_type,
        is_available=updated_user.driver_profile.is_available, # This will reflect current availability
        user=updated_user # This will be serialized by UserResponse schema
    )

@router.put("/profile/availability", response_model=DriverProfileResponse)
def update_driver_availability_route(
    availability_data: DriverAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current driver's availability status"""
    if current_user.role != "driver":
        raise HTTPException(status_code=403, detail="User is not a driver")

    updated_user = DriverService.update_driver_availability(db, current_user.id, availability_data.is_available)

    if not updated_user or not updated_user.driver_profile:
        raise HTTPException(status_code=404, detail="Driver profile not found or update failed")

    return DriverProfileResponse(
        driver_id=updated_user.driver_profile.driver_id,
        license_no=updated_user.driver_profile.license_no,
        vehicle_type=updated_user.driver_profile.vehicle_type,
        is_available=updated_user.driver_profile.is_available,
        user=updated_user
    )
