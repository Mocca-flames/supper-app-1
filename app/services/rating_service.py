import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from ..models.rating_models import DriverRating
from ..models.user_models import Driver
from ..models.order_models import Order, OrderStatus # Import Order and OrderStatus
from ..schemas.rating_schemas import DriverRatingCreate, DriverAverageRating

logger = logging.getLogger(__name__)

class RatingService:
    """Service layer for handling driver ratings."""

    def create_driver_rating(self, db: Session, client_id: str, rating_data: DriverRatingCreate) -> DriverRating:
        """
        Creates a new driver rating entry.
        """
        # 1. Verify driver exists
        driver = db.query(Driver).filter(Driver.driver_id == rating_data.driver_id).first()
        if not driver:
            logger.warning(f"Attempted to rate non-existent driver: {rating_data.driver_id}")
            raise HTTPException(status_code=404, detail="Driver not found.")

        # 2. Verify order exists, is completed, and is associated with the client and driver
        order = db.query(Order).filter(Order.id == rating_data.order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        
        if order.client_id != client_id:
            raise HTTPException(status_code=403, detail="Client is not associated with this order.")
            
        if order.driver_id != rating_data.driver_id:
            raise HTTPException(status_code=400, detail="Driver ID provided does not match the driver assigned to this order.")

        if order.status != OrderStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=f"Order status must be '{OrderStatus.COMPLETED.value}' to submit a rating.")

        # 3. Check if rating already exists for this order (enforced by unique constraint, but good to check explicitly)
        existing_rating = db.query(DriverRating).filter(DriverRating.order_id == rating_data.order_id).first()
        if existing_rating:
            raise HTTPException(status_code=409, detail="This order has already been rated.")

        # 4. Create new rating object
        new_rating = DriverRating(
            driver_id=rating_data.driver_id,
            client_id=client_id,
            order_id=rating_data.order_id,
            rating=rating_data.rating
        )

        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        logger.info(f"Client {client_id} successfully rated order {rating_data.order_id} for driver {rating_data.driver_id} with {rating_data.rating} stars.")
        
        # Note: Average rating calculation will be handled separately or triggered after this.
        
        return new_rating

    def get_driver_average_rating(self, db: Session, driver_id: str) -> DriverAverageRating:
        """
        Calculates and returns the average rating and total count for a specific driver.
        """
        # 1. Verify driver exists
        driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found.")

        # 2. Calculate average rating and count
        rating_stats = db.query(
            func.avg(DriverRating.rating).label('average_rating'),
            func.count(DriverRating.id).label('total_ratings')
        ).filter(DriverRating.driver_id == driver_id).first()

        average_rating = rating_stats.average_rating if rating_stats.average_rating is not None else None
        total_ratings = rating_stats.total_ratings if rating_stats.total_ratings is not None else 0

        if average_rating is not None:
            # Round to 2 decimal places
            average_rating = round(float(average_rating), 2)

        return DriverAverageRating(
            driver_id=driver_id,
            average_rating=average_rating,
            total_ratings=total_ratings
        )

rating_service = RatingService()