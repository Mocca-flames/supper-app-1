from fastapi import APIRouter, Depends, HTTPException, Path # Added Path
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.user_service import UserService
from ..services.order_service import OrderService # Added
from ..schemas.user_schemas import DriverResponse, UserResponse, User # Added User for type hint consistency
from ..schemas.order_schemas import AdminOrderCreate, OrderResponse # Added

router = APIRouter(prefix="/admin", tags=["Admin"])

# Simple admin authentication - in production, implement proper admin roles
def verify_admin_key(admin_key: str = None):
    if admin_key != "admin_secret_key_123":  # Change this!
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

# Removed /drivers/pending and /drivers/{driver_id}/approve endpoints
# as driver approval is no longer required for V1.

@router.get("/drivers", response_model=List[DriverResponse])
def get_all_drivers(
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key) # Ensure admin access
):
    """Admin retrieves all driver profiles."""
    drivers_users = UserService.get_all_drivers(db)
    # The UserService.get_all_drivers returns a list of User objects.
    # We need to construct DriverResponse objects from these.
    # This assumes that the User objects will have their driver_profile relationship loaded
    # or accessible, which is typical if the DriverResponse schema expects it.
    
    response_drivers = []
    for user in drivers_users:
        if user.driver_profile: # Ensure the driver profile exists
            response_drivers.append(
                DriverResponse(
                    driver_id=user.driver_profile.driver_id,
                    license_no=user.driver_profile.license_no,
                    vehicle_type=user.driver_profile.vehicle_type,
                    is_available=user.driver_profile.is_available,
                    user=user # UserResponse will be constructed from this User object
                )
            )
    return response_drivers

@router.post("/orders", response_model=OrderResponse)
def admin_create_order(
    order_data: AdminOrderCreate,
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin creates an order for a specific client"""
    try:
        # AdminOrderCreate schema includes client_id and inherits other fields from OrderCreate
        order = OrderService.create_order(db, order_data=order_data)
        return order
    except ValueError as e: # Catch potential errors from service layer
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/orders", response_model=List[OrderResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin retrieves all orders."""
    orders = OrderService.get_all_orders(db)
    return orders

@router.get("/clients", response_model=List[UserResponse])
def get_all_clients(
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin retrieves all clients."""
    clients = UserService.get_all_clients(db)
    return clients

@router.patch("/orders/{order_id}/cancel", response_model=OrderResponse)
def admin_cancel_order(
    order_id: str = Path(..., title="The ID of the order to cancel"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key) # Ensure admin access
):
    """
    Admin cancels the specified order.
    """
    try:
        # For admin, client_id is not checked for ownership, is_admin=True bypasses that
        order = OrderService.cancel_order(db, order_id, client_id=None, is_admin=True)
        return order
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else: # e.g., "Order cannot be cancelled"
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="An unexpected error occurred while cancelling the order.")
