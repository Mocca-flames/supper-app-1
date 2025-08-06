import logging # Added logging
from typing import List # Added List for type hinting
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException # Added HTTPException
from ..models.user_models import User, Client, Driver
from ..schemas.user_schemas import UserCreate, ClientCreate, DriverCreate, UserProfileUpdate, ClientProfileUpdate, DriverProfileUpdate # Added update schemas
from ..auth.firebase_auth import FirebaseAuth

logger = logging.getLogger(__name__) # Added logger instance

class UserService:
    @staticmethod
    def create_user_from_firebase(db: Session, firebase_uid: str, user_type: str) -> User:  # Added user_type
        # Get user info from Firebase first to get the email
        firebase_user = FirebaseAuth.get_user_info(firebase_uid)
        user_email = firebase_user.get("email")

        if not user_email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Firebase")

        # Try to fetch the user from the database by email.
        existing_user = db.query(User).filter(User.email == user_email).first()

        if existing_user:
            # If the user already exists with this email:
            # Check if the firebase_uid is different and update if necessary.
            if existing_user.id != firebase_uid:
                # Update the user ID if it's different
                existing_user.id = firebase_uid
                logger.info(f"Updating user ID for email {user_email} from {existing_user.id} to {firebase_uid}")

            # Update the role if it's different
            if existing_user.role != user_type:
                existing_user.role = user_type
                logger.info(f"Updating role for email {user_email} from {existing_user.role} to {user_type}")

            # Update other fields if they are different (e.g., display name, phone number)
            if existing_user.full_name != firebase_user.get("display_name"):
                existing_user.full_name = firebase_user.get("display_name")
                logger.info(f"Updating full_name for email {user_email}")
            if existing_user.phone_number != firebase_user.get("phone_number"):
                existing_user.phone_number = firebase_user.get("phone_number")
                logger.info(f"Updating phone_number for email {user_email}")

            try:
                db.add(existing_user)
                db.commit()
                db.refresh(existing_user)
                return existing_user
            except IntegrityError:
                db.rollback()
                # Handle potential concurrent updates or other integrity issues
                # Re-fetch and return if possible, or raise an error
                concurrently_updated_user = db.query(User).filter(User.email == user_email).first()
                if concurrently_updated_user:
                    return concurrently_updated_user
                else:
                    raise HTTPException(status_code=500, detail="Failed to update existing user due to integrity error")
            except Exception as e:
                db.rollback()
                logger.error(f"Unexpected error updating user for email {user_email}. Error: {str(e)}")
                raise HTTPException(status_code=500, detail="An unexpected error occurred while updating user profile.")
        else:
            # If the user does not exist, proceed to create them.
            new_user = User(
                id=firebase_uid,
                email=user_email,
                full_name=firebase_user.get("display_name"),
                phone_number=firebase_user.get("phone_number"),
                role=user_type  # Assign the user_type to the role attribute
            )
            
            try:
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user
            except IntegrityError:
                db.rollback()  # Important to rollback the session on error
                # The user might have been created by a concurrent request.
                # Try fetching again.
                concurrently_created_user = db.query(User).filter(User.id == firebase_uid).first()
                if concurrently_created_user:
                    return concurrently_created_user
                else:
                    # If it's still not there, then the IntegrityError was for some other reason,
                    # or something very unusual happened. Re-raise the original error.
                    raise

    @staticmethod
    def update_user_profile(db: Session, user_id: str, user_data: UserProfileUpdate) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_client_profile(db: Session, user_id: str, client_data: ClientCreate) -> Client:
        client = Client(
            client_id=user_id,
            home_address=client_data.home_address
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def update_client_profile(db: Session, user_id: str, client_data: ClientProfileUpdate) -> Client:
        client = db.query(Client).filter(Client.client_id == user_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client profile not found")

        for field, value in client_data.model_dump(exclude_unset=True).items():
            setattr(client, field, value)

        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    
    @staticmethod
    def create_driver_profile(db: Session, user_id: str, driver_data: DriverCreate) -> Driver:
        logger.info(f"UserService: Attempting to create driver profile for user_id: {user_id} with data: {driver_data.model_dump_json(exclude_none=True)}")
        driver = Driver(
            driver_id=user_id,
            license_no=driver_data.license_no,
            vehicle_type=driver_data.vehicle_type
        )
        try:
            db.add(driver)
            logger.info(f"UserService: Driver object for user_id: {user_id} added to session.")
            db.commit()
            logger.info(f"UserService: db.commit() successful for driver profile creation for user_id: {user_id}")
            db.refresh(driver)
            logger.info(f"UserService: db.refresh(driver) successful for user_id: {user_id}")
            return driver
        except IntegrityError as ie:
            db.rollback()
            logger.error(f"UserService: IntegrityError creating driver profile for user_id {user_id}. Error: {str(ie)}")
            # This detail might expose too much, consider a generic message for the client.
            # For now, let the route handler decide the final HTTP response detail.
            raise # Re-raise to be caught by the route handler, or raise specific HTTPException
        except Exception as e:
            db.rollback()
            logger.error(f"UserService: Unexpected error creating driver profile for user_id {user_id}. Type: {type(e).__name__}, Error: {str(e)}")
            raise # Re-raise to be caught by the route handler
    
    @staticmethod
    def update_driver_profile(db: Session, user_id: str, driver_data: DriverProfileUpdate) -> Driver:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.driver_profile:
            raise HTTPException(status_code=404, detail="Driver profile not found for this user")

        # Update User fields if provided
        for field, value in driver_data.model_dump(exclude_unset=True).items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Update Driver profile fields if provided
        for field, value in driver_data.model_dump(exclude_unset=True).items():
            if hasattr(user.driver_profile, field):
                setattr(user.driver_profile, field, value)

        db.add(user) # Add user and driver_profile to session
        db.commit()
        db.refresh(user)
        db.refresh(user.driver_profile)
        return user.driver_profile
    
    @staticmethod
    def update_driver_availability(db: Session, user_id: str, is_available: bool) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.driver_profile:
            raise HTTPException(status_code=404, detail="Driver profile not found")
        
        user.driver_profile.is_available = is_available
        db.add(user.driver_profile)
        db.commit()
        db.refresh(user) # Refresh user to get updated driver_profile
        return user

    @staticmethod
    def get_all_drivers(db: Session) -> List[User]:
        """Retrieve all users with the 'driver' role."""
        # Ensure driver_profile is loaded to be accessible for DriverResponse construction
        # This can be done via joinedload or selectinload if performance becomes an issue
        # For now, relying on SQLAlchemy's default lazy loading or Pydantic's attribute access.
        drivers = db.query(User).filter(User.role == "driver").all()
        return drivers

    @staticmethod
    def get_all_clients(db: Session) -> List[User]:
        """Retrieve all users with the 'client' role."""
        clients = db.query(User).filter(User.role == "client").all()
        return clients
