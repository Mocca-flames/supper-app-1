from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..services.order_service import OrderService
from ..schemas.order_schemas import TrackingSessionResponse, OrderResponse, OrderCreate
from ..schemas.user_schemas import DriverLocationResponse, UserResponse # Changed User to UserResponse
from ..auth.middleware import get_current_user # For client authentication

router = APIRouter(
    prefix="/orders", # This prefix will be combined with /api in main.py
    tags=["Orders"]
)

@router.post("/", response_model=OrderResponse)
def create_new_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Creates a new order with route calculation and ETA.
    """
    try:
        # Ensure the order is created by the authenticated client
        order_data.client_id = current_user.id
        order = OrderService.create_order(db, order_data)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/{order_id}/route", response_model=OrderResponse) # Assuming OrderResponse contains route details
def get_order_route_details(
    order_id: str = Path(..., title="The ID of the order to get route details for"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Returns detailed route information for a specific order.
    Accessible by the client who owns the order.
    """
    try:
        order = OrderService.get_order_by_id(db, order_id)
        if not order or order.client_id != current_user.id:
            raise HTTPException(status_code=404, detail="Order not found or access denied.")
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/{order_id}/recalculate-route", response_model=OrderResponse)
def recalculate_order_route(
    order_id: str = Path(..., title="The ID of the order to recalculate route for"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Triggers route recalculation for an order with current traffic conditions.
    Accessible by the client who owns the order.
    """
    try:
        order = OrderService.get_order_by_id(db, order_id)
        if not order or order.client_id != current_user.id:
            raise HTTPException(status_code=404, detail="Order not found or access denied.")
        
        # Recalculate route details
        updated_order = OrderService._calculate_order_details(order)
        db.add(updated_order)
        db.commit()
        db.refresh(updated_order)
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/{order_id}/track", response_model=TrackingSessionResponse)
def track_order(
    order_id: str = Path(..., title="The ID of the order to track"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Starts real-time tracking for the specified order.
    Accessible by the client who owns the order.
    """
    try:
        session_data = OrderService.start_order_tracking(db, order_id, current_user.id)
        return session_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while starting tracking.")

@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order_client(
    order_id: str = Path(..., title="The ID of the order to cancel"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Cancels the specified order.
    Accessible by the client who owns the order.
    """
    try:
        order = OrderService.cancel_order(db, order_id, client_id=current_user.id, is_admin=False)
        return order
    except ValueError as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while cancelling the order.")

@router.get("/{order_id}/location", response_model=Optional[DriverLocationResponse])
def get_order_driver_location_client(
    order_id: str = Path(..., title="The ID of the order for which to get driver location"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Returns the current driver location for an order.
    Used for real-time map tracking by the client who owns the order.
    Returns null if driver is not yet assigned or location is not available.
    """
    try:
        location = OrderService.get_order_driver_location(db, order_id, current_user.id)
        if location is None:
            return None 
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching driver location.")
