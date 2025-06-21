import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException
from ..config import settings

# Initialize Firebase Admin SDK
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

class FirebaseAuth:
    @staticmethod
    def verify_firebase_token(token: str) -> str:
        """Verify Firebase token and return user ID"""
        try:
            # Allow a clock skew of 10 seconds to accommodate minor differences
            decoded_token = auth.verify_id_token(token, clock_skew_seconds=60)
            return decoded_token["uid"]
        except Exception as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid Firebase token | Time Discrepencies: {str(e)}"
            )
    
    @staticmethod
    def get_user_info(uid: str):
        """Get user info from Firebase"""
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "phone_number": user.phone_number,
                "display_name": user.display_name
            }
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"User not found: {str(e)}"
            )
