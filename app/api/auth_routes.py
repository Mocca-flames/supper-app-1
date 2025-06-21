import logging # Added for logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schemas import UserResponse, ClientCreate, ClientResponse, DriverCreate, DriverResponse, UserRole # Added UserRole
from ..auth.middleware import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register_user(
    firebase_uid: str,
    user_type: UserRole,  # Changed to UserRole Enum for validation
    db: Session = Depends(get_db)
):
    """Register a new user from Firebase UID, specifying their type (client or driver)."""
    logger.info(f"Attempting to register user with firebase_uid: {firebase_uid}, user_type: {user_type.value}")
    try:
        user = UserService.create_user_from_firebase(db, firebase_uid, user_type.value)  # Pass enum's value
        logger.info(f"Successfully registered user: {user.id} with firebase_uid: {firebase_uid}")
        return user
    except HTTPException as http_exc:
        logger.error(f"HTTPException during registration for firebase_uid {firebase_uid}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during registration for firebase_uid {firebase_uid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during user registration.")

@router.post("/client-profile", response_model=ClientResponse)
def create_client_profile(
    client_data: ClientCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create client profile for current user"""
    logger.info(f"Attempting to create client profile for user_id: {current_user.id}")
    try:
        if current_user.client_profile:
            logger.warning(f"Client profile already exists for user_id: {current_user.id}")
            raise HTTPException(status_code=400, detail="Client profile already exists")
        
        client = UserService.create_client_profile(db, current_user.id, client_data)
        logger.info(f"Successfully created client profile for user_id: {current_user.id}, client_id: {client.id}")
        return client
    except HTTPException as http_exc:
        logger.error(f"HTTPException during client profile creation for user_id {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during client profile creation for user_id {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during client profile creation.")

@router.post("/driver-profile", response_model=DriverResponse)
def create_driver_profile(
    driver_data: DriverCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create driver profile for current user"""
    logger.info(f"Attempting to create driver profile for user_id: {current_user.id}")
    try:
        if current_user.driver_profile:
            logger.warning(f"Driver profile already exists for user_id: {current_user.id}")
            raise HTTPException(status_code=400, detail="Driver profile already exists")
        
        driver = UserService.create_driver_profile(db, current_user.id, driver_data)
        logger.info(f"Successfully created driver profile for user_id: {current_user.id}, driver_id: {driver.id}")
        return driver
    except HTTPException as http_exc:
        logger.error(f"HTTPException during driver profile creation for user_id {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during driver profile creation for user_id {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during driver profile creation.")

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    logger.info(f"Attempting to retrieve info for user_id: {current_user.id}")
    try:
        # Assuming current_user object itself is what needs to be returned
        # and no specific service call is needed here beyond what Depends(get_current_user) does.
        logger.info(f"Successfully retrieved info for user_id: {current_user.id}")
        return current_user
    except HTTPException as http_exc: # Should not happen if get_current_user handles its own errors
        logger.error(f"HTTPException during get_current_user_info for user_id {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error during get_current_user_info for user_id {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving user information.")
