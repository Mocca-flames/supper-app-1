from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..services.order_service import OrderService
from ..schemas.order_schemas import TrackingSessionResponse, OrderResponse
from ..schemas.user_schemas import DriverLocationResponse, UserResponse # Changed User to UserResponse
from ..auth.middleware import get_current_user # For client authentication

router = APIRouter(
    prefix="/orders", # This prefix will be combined with /api in main.py
    tags=["Orders"]
)

@router.post("/{order_id}/track", response_model=TrackingSessionResponse)
def track_order(
    order_id: str = Path(..., title="The ID of the order to track"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user) # Changed User to UserResponse
):
    """
    Starts real-time tracking for the specified order.
    Accessible by the client who owns the order.
    """
    try:
        session_data = OrderService.start_order_tracking(db, order_id, current_user.id)
        return session_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) # 404 if order not found/access denied, or 400 for bad status
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="An unexpected error occurred while starting tracking.")

@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order_client(
    order_id: str = Path(..., title="The ID of the order to cancel"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user) # Changed User to UserResponse
):
    """
    Cancels the specified order.
    Accessible by the client who owns the order.
    """
    try:
        order = OrderService.cancel_order(db, order_id, client_id=current_user.id, is_admin=False)
        return order
    except ValueError as e:
        # Distinguish between "not found" and "cannot cancel"
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else: # e.g., "Order cannot be cancelled"
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="An unexpected error occurred while cancelling the order.")

@router.get("/{order_id}/location", response_model=Optional[DriverLocationResponse])
def get_order_driver_location_client(
    order_id: str = Path(..., title="The ID of the order for which to get driver location"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user) # Changed User to UserResponse
):
    """
    Returns the current driver location for an order.
    Used for real-time map tracking by the client who owns the order.
    Returns null if driver is not yet assigned or location is not available.
    """
    try:
        location = OrderService.get_order_driver_location(db, order_id, current_user.id)
        if location is None:
            # This is an expected case, not an error.
            # Client can interpret null as "location not available yet".
            # If order itself doesn't exist or no access, service layer raises ValueError.
            return None 
        return location
    except ValueError as e: # Raised by service if order not found or access denied
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching driver location.")
