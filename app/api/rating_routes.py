import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.rating_schemas import DriverRatingCreate, DriverRatingResponse, DriverAverageRating
from ..services.rating_service import rating_service
from ..auth.middleware import get_current_user_id, get_current_client_id

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ratings/drivers", response_model=DriverRatingResponse, status_code=status.HTTP_201_CREATED, tags=["Ratings"])
def submit_driver_rating(
    rating_data: DriverRatingCreate,
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Allows a client to submit a 5-star rating for a driver.
    Requires client authentication.
    """
    try:
        new_rating = rating_service.create_driver_rating(db, client_id, rating_data)
        return new_rating
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error submitting driver rating: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while submitting rating.")

@router.get("/ratings/drivers/{driver_id}/average", response_model=DriverAverageRating, tags=["Ratings"])
def get_driver_rating_summary(
    driver_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the average rating and total number of ratings for a specific driver.
    """
    try:
        summary = rating_service.get_driver_average_rating(db, driver_id)
        return summary
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving driver rating summary for {driver_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while retrieving rating summary.")