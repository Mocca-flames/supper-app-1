from sqlalchemy.orm import Session
from ..models.order_models import Order
from ..models.user_models import User, Driver  # Added User and Driver models
from ..schemas.order_schemas import OrderAccept, OrderStatusUpdate
from ..schemas.user_schemas import DriverLocationUpdate, DriverProfileUpdate # Added DriverProfileUpdate
from ..utils.redis_client import RedisService

class DriverService:
    @staticmethod
    def get_pending_orders(db: Session):
        """Get all pending orders for drivers"""
        return db.query(Order).filter(Order.status == 'pending').all()

    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept):
        """Accept an order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.driver_id = accept_data.driver_id
            order.status = 'accepted'
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def get_driver_orders(db: Session, driver_id: str):
        """Get all orders for the current driver"""
        return db.query(Order).filter(Order.driver_id == driver_id).all()

    @staticmethod
    def update_order_status(db: Session, order_id: str, status: str):
        """Update order status"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_location(driver_id: str, location_data: DriverLocationUpdate):
        """Update driver location"""
        RedisService.set_driver_location(
            driver_id,
            location_data.latitude,
            location_data.longitude
        )

    @staticmethod
    def update_driver_profile(db: Session, driver_id: str, profile_data: DriverProfileUpdate):
        """Update driver profile information, excluding availability."""
        user = db.query(User).filter(User.id == driver_id, User.role == "driver").first()
        if not user:
            return None  # Or raise HTTPException

        driver_profile = user.driver_profile
        if not driver_profile:
            # This case should ideally not happen if user.role == "driver"
            # and data is consistent. Consider creating one if it's a valid scenario.
            return None # Or raise HTTPException

        updated_user_data = profile_data.model_dump(exclude_unset=True)

        user_fields = ["email", "full_name", "phone_number"]
        # "is_available" is removed from here as it's handled by a separate method
        driver_fields = ["license_no", "vehicle_type"]

        user_updated = False
        driver_updated = False

        for key, value in updated_user_data.items():
            if key in user_fields:
                setattr(user, key, value)
                user_updated = True
            elif key in driver_fields:
                setattr(driver_profile, key, value)
                driver_updated = True
        
        if user_updated or driver_updated:
            db.commit()
            db.refresh(user)
            if driver_updated: # Also refresh driver_profile if it was changed
                 db.refresh(driver_profile)
        
        return user # We will construct DriverResponse in the route

    @staticmethod
    def update_driver_availability(db: Session, driver_id: str, is_available: bool):
        """Update driver's availability status"""
        user = db.query(User).filter(User.id == driver_id, User.role == "driver").first()
        if not user or not user.driver_profile:
            return None # Or raise HTTPException
        
        driver_profile = user.driver_profile
        driver_profile.is_available = is_available
        db.commit()
        db.refresh(user)
        db.refresh(driver_profile)
        return user
