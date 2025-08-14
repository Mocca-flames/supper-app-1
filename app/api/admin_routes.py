from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from ..database import get_db
from ..services.user_service import UserService
from ..services.order_service import OrderService
from ..schemas.user_schemas import DriverResponse, UserResponse
from ..schemas.order_schemas import AdminOrderCreate, OrderResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# Simple admin authentication - in production, implement proper admin roles
def verify_admin_key(admin_key: str = None):
    if admin_key != "Maurice@12!":  # Change this!
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

# ============= EXISTING ENDPOINTS =============

@router.get("/drivers", response_model=List[DriverResponse])
def get_all_drivers(
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin retrieves all driver profiles with names and emails."""
    drivers_users = UserService.get_all_drivers(db)

    response_drivers = []
    for user in drivers_users:
        if user.driver_profile:
            response_drivers.append(
                DriverResponse(
                    driver_id=user.driver_profile.driver_id,
                    license_no=user.driver_profile.license_no,
                    vehicle_type=user.driver_profile.vehicle_type,
                    is_available=user.driver_profile.is_available,
                    email=user.email,
                    full_name=user.full_name
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
        order = OrderService.create_order(db, order_data=order_data)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
    """Admin retrieves all clients with relevant data."""
    clients = UserService.get_all_clients(db)
    response_clients = []
    for client in clients:
        response_clients.append({
            "id": client.id,
            "client_id": client.id,
            "full_name": client.full_name,
            "email": client.email,
            "phone_number": client.phone_number,
            "created_at": client.created_at,
        })
    return response_clients

@router.delete("/orders/{order_id}", response_model=OrderResponse)
def admin_delete_order(
    order_id: str = Path(..., title="The ID of the order to delete"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin deletes the specified order."""
    try:
        order = OrderService.delete_order(db, order_id, is_admin=True)
        return order
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the order.")

# ============= NEW ADMIN CONTROL ENDPOINTS =============

@router.post("/pricing/calculate")
def calculate_price_preview(
    distance_km: Decimal = Query(..., description="Distance in kilometers", ge=0),
    rate_per_km: Optional[Decimal] = Query(None, description="Custom rate per km (optional)"),
    minimum_fare: Optional[Decimal] = Query(None, description="Custom minimum fare (optional)"),
    admin_verified = Depends(verify_admin_key)
):
    """Calculate price preview with optional custom rates."""
    try:
        # Validate inputs
        if distance_km < 0:
            raise HTTPException(status_code=400, detail="Distance cannot be negative")

        # Get current pricing configuration from PricingService
        from app.services.pricing_service import PricingService
        pricing = PricingService.get_current_pricing()

        # Use current pricing as defaults, but allow overrides
        if rate_per_km is None:
            rate_per_km = pricing["rate_per_km"]
        elif rate_per_km < 0:
            raise HTTPException(status_code=400, detail="Rate per km cannot be negative")

        if minimum_fare is None:
            minimum_fare = pricing["minimum_fare"]
        elif minimum_fare < 0:
            raise HTTPException(status_code=400, detail="Minimum fare cannot be negative")

        calculated_price = distance_km * rate_per_km
        final_price = max(calculated_price, minimum_fare)

        return {
            "distance_km": float(distance_km),
            "rate_per_km": float(rate_per_km),
            "minimum_fare": float(minimum_fare),
            "calculated_price": float(calculated_price),
            "final_price": float(final_price),
            "minimum_fare_applied": calculated_price < minimum_fare
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Price calculation failed: {str(e)}")

@router.patch("/orders/{order_id}/price", response_model=OrderResponse)
def admin_override_order_price(
    order_id: str = Path(..., title="The ID of the order to update"),
    new_price: Decimal = Query(..., description="New price for the order", ge=0),
    reason: Optional[str] = Query(None, description="Reason for price override"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin override: manually set order price."""
    try:
        # You'll need to add this method to OrderService
        order = OrderService.admin_update_price(db, order_id, new_price, reason)
        return order
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to override order price: {str(e)}")

@router.patch("/orders/{order_id}/status")
def admin_update_order_status(
    order_id: str = Path(..., title="The ID of the order to update"),
    new_status: str = Query(..., description="New status for the order"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin update order status."""
    try:
        # Convert string to OrderStatus enum
        try:
            from ..models.order_models import OrderStatus
            order_status_enum = OrderStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {new_status}")

        # You'll need to add this method to OrderService
        order = OrderService.admin_update_status(db, order_id, order_status_enum)
        return {"message": f"Order {order_id} status updated to {new_status}"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")

@router.get("/orders/search")
def search_orders(
    client_email: Optional[str] = Query(None, description="Search by client email"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price filter"),
    limit: int = Query(50, description="Number of results to return", ge=1, le=500),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Search and filter orders."""
    try:
        # You'll need to add this method to OrderService
        orders = OrderService.search_orders(db, {
            "client_email": client_email,
            "status": status,
            "min_price": min_price,
            "max_price": max_price
        }, limit)
        return {"total_found": len(orders), "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search orders: {str(e)}")

@router.get("/stats/summary")
def get_admin_stats_summary(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Get basic admin statistics."""
    try:
        # You'll need to add this method to OrderService
        stats = OrderService.get_admin_stats(db, days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/drivers/{driver_id}/toggle-availability")
def toggle_driver_availability(
    driver_id: str = Path(..., title="The ID of the driver"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin toggle driver availability status."""
    try:
        # You'll need to add this method to UserService
        driver = UserService.admin_toggle_driver_availability(db, driver_id)
        return {
            "message": f"Driver availability toggled",
            "driver_id": driver_id,
            "is_available": driver.driver_profile.is_available if driver.driver_profile else False
        }
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle driver availability: {str(e)}")

# ============= SIMPLE PRICING PRESETS =============

@router.post("/pricing/preset/{preset}")
def apply_pricing_preset(
    preset: str = Path(..., title="Pricing preset: rush_hour, off_peak, weekend"),
    admin_verified = Depends(verify_admin_key)
):
    """Apply simple pricing presets for strategic control."""
    from app.services.pricing_service import PricingService

    # Set the pricing preset in the central service
    PricingService.set_pricing_preset(preset)

    # Get the current pricing to return
    pricing = PricingService.get_current_pricing()

    return {
        "preset_applied": preset,
        "rate_per_km": pricing["rate_per_km"],
        "minimum_fare": pricing["minimum_fare"],
        "message": f"Applied {preset} pricing preset"
    }

@router.get("/pricing/presets")
def get_pricing_presets(admin_verified = Depends(verify_admin_key)):
    """Get available pricing presets."""
    return {
        "presets": {
            "rush_hour": {"rate_per_km": "15.00", "minimum_fare": "70.00", "description": "Peak hours pricing"},
            "off_peak": {"rate_per_km": "8.00", "minimum_fare": "40.00", "description": "Off-peak discount pricing"},
            "weekend": {"rate_per_km": "12.00", "minimum_fare": "60.00", "description": "Weekend standard pricing"},
            "standard": {"rate_per_km": "10.00", "minimum_fare": "50.00", "description": "Default pricing"}
        }
    }

@router.post("/orders/create-with-custom-price", response_model=OrderResponse)
def admin_create_order_custom_price(
    order_data: AdminOrderCreate,
    custom_price: Optional[Decimal] = Query(None, description="Override calculated price"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Admin creates an order with optional custom pricing."""
    try:
        # You'll need to modify OrderService.create_order to accept custom_price parameter
        order = OrderService.create_order(db, order_data=order_data, admin_custom_price=custom_price)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/orders/{order_id}/price-breakdown")
def get_order_price_breakdown(
    order_id: str = Path(..., title="The ID of the order"),
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Get detailed price breakdown for an order."""
    try:
        # You'll need to add this method to OrderService
        breakdown = OrderService.get_price_breakdown(db, order_id)
        return breakdown
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get price breakdown: {str(e)}")