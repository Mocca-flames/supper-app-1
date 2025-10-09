from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from .firebase_auth import FirebaseAuth
from ..database import get_db
from ..models.user_models import User

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Expected format: "Bearer <token>"
        token = authorization.split(" ")[1]
        firebase_uid = FirebaseAuth.verify_firebase_token(token)
    
        # Get user from database, eagerly loading client and driver profiles
        user = db.query(User).options(
            joinedload(User.client_profile),
            joinedload(User.driver_profile)
        ).filter(User.id == firebase_uid).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")
        
        return user
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

def get_current_client(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current client profile"""
    if not current_user.client_profile:
        raise HTTPException(status_code=403, detail="Client profile not found")
    return current_user.client_profile

def get_current_driver(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current driver profile"""
    if not current_user.driver_profile:
        raise HTTPException(status_code=403, detail="Driver profile not found")
    return current_user.driver_profile

# Removed get_approved_driver as approval is no longer required for V1.
# Driver routes will now use get_current_driver directly.

def get_current_user_id(current_user: User = Depends(get_current_user)) -> str:
    """Get the ID of the current authenticated user."""
    return current_user.id

def get_current_client_id(client_profile = Depends(get_current_client)) -> str:
    """Get the ID of the current authenticated client."""
    # Assuming client_profile object has a user_id attribute which is the client ID
    return client_profile.user_id
