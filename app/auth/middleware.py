from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
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
        
        # Get user from database
        user = db.query(User).filter(User.id == firebase_uid).first()
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
