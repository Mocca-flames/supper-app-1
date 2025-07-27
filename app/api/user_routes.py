from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schemas import UserResponse, UserProfileUpdate
from ..auth.middleware import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user = Depends(get_current_user)):
    """Get current user's complete profile information."""
    logger.info(f"Attempting to retrieve complete profile for user_id: {current_user.id}")
    try:
        # The current_user object already has client_profile and driver_profile loaded if they exist
        # due to the relationships defined in the User model and Pydantic's from_attributes.
        logger.info(f"Successfully retrieved complete profile for user_id: {current_user.id}")
        return current_user
    except HTTPException as http_exc:
        logger.error(f"HTTPException during get_user_profile for user_id {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during get_user_profile for user_id {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving user profile.")

@router.put("/profile", response_model=UserResponse)
def update_user_profile_route(
    user_data: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's general profile information."""
    logger.info(f"Attempting to update user profile for user_id: {current_user.id}")
    try:
        updated_user = UserService.update_user_profile(db, current_user.id, user_data)
        # Refresh the user object to ensure relationships are loaded for the response
        db.refresh(updated_user)
        logger.info(f"Successfully updated user profile for user_id: {current_user.id}")
        return updated_user
    except HTTPException as http_exc:
        logger.error(f"HTTPException during user profile update for user_id {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during user profile update for user_id {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during user profile update.")
