from decimal import Decimal
import logging # Added logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException

from app.models.order_models import Order, OrderStatus # Added HTTPException
from ..models.user_models import User, Client, Driver
from ..schemas.user_schemas import UserCreate, ClientCreate, DriverCreate, UserProfileUpdate, ClientProfileUpdate, DriverProfileUpdate, FCMTokenUpdate # Added update schemas
from ..auth.firebase_auth import FirebaseAuth

logger = logging.getLogger(__name__) # Added logger instance

class UserService:
    @staticmethod
    def create_user_from_firebase(db: Session, firebase_uid: str, user_type: str) -> User:
        """Create or update user from Firebase authentication."""
        if not firebase_uid or not user_type:
            raise HTTPException(status_code=400, detail="Missing required firebase_uid or user_type") from e

        # Get user info from Firebase first to get the email
        firebase_user = FirebaseAuth.get_user_info(firebase_uid)
        user_email = firebase_user.get("email")

        if not user_email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Firebase") from e

        try:
            # Use a single transaction to prevent race conditions
            existing_user = db.query(User).filter(User.email == user_email).first()

            if existing_user:
                # Update existing user if needed
                if existing_user.id != firebase_uid:
                    logger.info(f"Updating user ID for email {user_email} from {existing_user.id} to {firebase_uid}")

                    # First update any references to this user in the drivers table
                    if existing_user.driver_profile:
                        existing_user.driver_profile.driver_id = firebase_uid
                        db.add(existing_user.driver_profile)
                        logger.info(f"Updated driver profile reference for user {user_email}")

                    # Also update any references in the clients table
                    if existing_user.client_profile:
                        existing_user.client_profile.client_id = firebase_uid
                        db.add(existing_user.client_profile)
                        logger.info(f"Updated client profile reference for user {user_email}")

                    # Now update the user's ID
                    existing_user.id = firebase_uid

                if existing_user.role != user_type:
                    existing_user.role = user_type
                    logger.info(f"Updating role for email {user_email} from {existing_user.role} to {user_type}")

                # Update other fields if they are different
                if existing_user.full_name != firebase_user.get("display_name"):
                    existing_user.full_name = firebase_user.get("display_name")
                    logger.info(f"Updating full_name for email {user_email}")
                firebase_phone_number = firebase_user.get("phone_number")
                logger.info(f"Existing phone_number for {user_email}: {existing_user.phone_number}. Firebase phone_number: {firebase_phone_number}")
                
                # Only update phone_number if the Firebase value is not None AND it's different from the existing value.
                # OR if the existing value is None and the Firebase value is not None.
                # However, for this bug, we must ensure we DO NOT overwrite a non-null DB value with a null Firebase value.
                if firebase_phone_number is not None and existing_user.phone_number != firebase_phone_number:
                    existing_user.phone_number = firebase_phone_number
                    logger.info(f"Updating phone_number for email {user_email} to {firebase_phone_number}")
                elif existing_user.phone_number is not None and firebase_phone_number is None:
                    # Log the potential overwrite but DO NOT perform the update yet.
                    logger.info(f"Skipping phone_number update for {user_email}: DB value is present, Firebase value is None. Retaining DB value.")
                elif existing_user.phone_number is None and firebase_phone_number is not None:
                    # If DB is null but Firebase has a value, update it.
                    existing_user.phone_number = firebase_phone_number
                    logger.info(f"Updating phone_number for email {user_email} from None to {firebase_phone_number}")
                
                db.add(existing_user)
                db.commit()
                db.refresh(existing_user)
                return existing_user
            else:
                # Create new user
                new_user = User(
                    id=firebase_uid,
                    email=user_email,
                    full_name=firebase_user.get("display_name"),
                    phone_number=firebase_user.get("phone_number"),
                    role=user_type
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                return new_user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating user from Firebase: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create/update user from Firebase: {str(e)}") 

    @staticmethod
    def update_user_profile(db: Session, user_id: str, user_data: UserProfileUpdate) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_fcm_token(db: Session, user_id: str, fcm_token_data: FCMTokenUpdate) -> User:
        """Update the FCM token for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}")

        user.fcm_token = fcm_token_data.fcmToken

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
            raise HTTPException(status_code=404, detail=f"Client profile not found for user: {user_id}") 

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
            raise HTTPException(status_code=404, detail=f"User not found: {user_id}") from e
        if not user.driver_profile:
            raise HTTPException(status_code=404, detail=f"Driver profile not found for user: {user_id}") from e

        # Update User fields if provided
        for field, value in driver_data.model_dump(exclude_unset=True).items():
            if hasattr(user, field):
                setattr(user, field, value)

        # Update Driver profile fields if provided
        for field, value in driver_data.model_dump(exclude_unset=True).items():
            if hasattr(user.driver_profile, field):
                setattr(user.driver_profile, field, value)

        try:
            db.add(user) # Add user and driver_profile to session
            db.commit()
            db.refresh(user)
            db.refresh(user.driver_profile)
            return user.driver_profile
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Unexpected error updating driver profile for user {user_id}. Error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update driver profile for user: {user_id}")
    
    @staticmethod
    def update_driver_availability(db: Session, user_id: str, is_available: bool) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.driver_profile:
            raise HTTPException(status_code=404, detail=f"Driver profile not found for user: {user_id}")
        
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
    
    @staticmethod
    def admin_toggle_driver_availability(db: Session, driver_id: str) -> Dict[str, Any]:
        """Admin toggle driver availability with comprehensive logging"""
        logger.info(f"👑 ===== ADMIN DRIVER AVAILABILITY TOGGLE =====")
        logger.info(f"🚗 Driver ID: {driver_id}")

        try:
            # Find the driver directly (based on your existing Driver model)
            driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
            
            if not driver:
                logger.error(f"❌ Driver not found: {driver_id}")
                raise ValueError(f"Driver with ID {driver_id} not found")

            # Toggle availability
            current_status = driver.is_available
            driver.is_available = not current_status
            
            logger.info(f"🚗 Admin toggled driver {driver_id} availability: {current_status} → {not current_status}")
            
            db.commit()
            db.refresh(driver)

            # Prepare response
            result = {
                "driver_id": driver_id,
                "previous_status": current_status,
                "new_status": driver.is_available,
                "action": "enabled" if driver.is_available else "disabled"
            }

            logger.info(f"✅ Driver availability updated successfully: {result['action']}")
            logger.info("🎉 ===== DRIVER AVAILABILITY TOGGLE COMPLETED =====")
            
            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during driver availability toggle: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during availability toggle: {str(e)}") from e

    @staticmethod
    def get_all_drivers_status(db: Session, include_inactive: bool = True) -> List[Dict[str, Any]]:
        """Get status overview of all drivers for admin dashboard"""
        try:
            query = db.query(Driver)

            if not include_inactive:
                query = query.filter(Driver.is_available == True)

            drivers = query.all()

            drivers_status = []
            for driver in drivers:
                driver_info = {
                    "driver_id": driver.driver_id,
                    "is_available": driver.is_available,
                    "status": "available" if driver.is_available else "unavailable",
                    # Add more fields as needed from your Driver model
                    # "name": driver.name if hasattr(driver, 'name') else None,
                    # "email": driver.email if hasattr(driver, 'email') else None,
                    # "phone": driver.phone if hasattr(driver, 'phone') else None,
                    # "vehicle_type": driver.vehicle_type if hasattr(driver, 'vehicle_type') else None,
                    # "created_at": driver.created_at.isoformat() if hasattr(driver, 'created_at') else None
                }
                drivers_status.append(driver_info)

            return drivers_status

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error fetching drivers status: {str(e)}")
            raise ValueError(f"Error fetching drivers status: {str(e)}") from e

    @staticmethod
    def get_driver_performance_stats(db: Session, driver_id: str, days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for a specific driver"""
        logger.info(f"📊 ===== DRIVER PERFORMANCE STATS =====")
        logger.info(f"🚗 Driver ID: {driver_id}")
        logger.info(f"📅 Period: {days} days")

        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # Verify driver exists
            driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
            if not driver:
                logger.error(f"❌ Driver not found: {driver_id}")
                raise ValueError(f"Driver with ID {driver_id} not found")

            # Get driver's orders in the period
            driver_orders = db.query(Order)\
                .filter(Order.driver_id == driver_id)\
                .filter(Order.created_at >= cutoff_date)\
                .all()

            # Calculate stats
            total_orders = len(driver_orders)
            completed_orders = [o for o in driver_orders if o.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED]]
            total_earnings = sum(order.price for order in completed_orders)
            
            # Orders by status
            orders_by_status = {}
            for order in driver_orders:
                status = order.status.value
                orders_by_status[status] = orders_by_status.get(status, 0) + 1

            # Average earnings per completed order
            avg_earnings = total_earnings / len(completed_orders) if completed_orders else Decimal("0")

            # Completion rate
            completion_rate = (len(completed_orders) / total_orders * 100) if total_orders > 0 else 0

            stats = {
                "driver_id": driver_id,
                "period_days": days,
                "period_start": cutoff_date.date().isoformat(),
                "period_end": datetime.now().date().isoformat(),
                "total_orders": total_orders,
                "completed_orders": len(completed_orders),
                "total_earnings": float(total_earnings),
                "average_earnings_per_order": float(avg_earnings),
                "completion_rate_percent": round(completion_rate, 2),
                "orders_by_status": orders_by_status,
                "current_availability": driver.is_available
            }

            logger.info(f"📊 Performance stats generated:")
            logger.info(f"   • Total orders: {total_orders}")
            logger.info(f"   • Completed: {len(completed_orders)}")
            logger.info(f"   • Earnings: R{total_earnings}")
            logger.info(f"   • Completion rate: {completion_rate:.1f}%")

            return stats

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating driver stats: {str(e)}")
            raise ValueError(f"Error generating driver performance stats: {str(e)}") from e

    @staticmethod
    def admin_bulk_update_drivers(db: Session, driver_ids: List[str], action: str) -> Dict[str, Any]:
        """Bulk update multiple drivers (enable/disable availability)"""
        logger.info(f"👑 ===== ADMIN BULK DRIVER UPDATE =====")
        logger.info(f"🚗 Driver IDs: {driver_ids}")
        logger.info(f"⚡ Action: {action}")

        if action not in ["enable", "disable"]:
            raise ValueError("Action must be 'enable' or 'disable'")

        try:
            updated_drivers = []
            failed_drivers = []
            
            for driver_id in driver_ids:
                try:
                    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
                    
                    if not driver:
                        failed_drivers.append({
                            "driver_id": driver_id,
                            "reason": "Driver not found"
                        })
                        continue

                    old_status = driver.is_available
                    new_status = action == "enable"
                    
                    if old_status != new_status:
                        driver.is_available = new_status
                        updated_drivers.append({
                            "driver_id": driver_id,
                            "previous_status": old_status,
                            "new_status": new_status,
                            "changed": True
                        })
                        logger.debug(f"✅ Updated {driver_id}: {old_status} → {new_status}")
                    else:
                        updated_drivers.append({
                            "driver_id": driver_id,
                            "previous_status": old_status,
                            "new_status": new_status,
                            "changed": False
                        })
                        logger.debug(f"ℹ️ No change needed for {driver_id}: already {new_status}")

                except Exception as e:
                    failed_drivers.append({
                        "driver_id": driver_id,
                        "reason": str(e)
                    })
                    logger.warning(f"⚠️ Failed to update {driver_id}: {str(e)}")

            # Commit all changes
            db.commit()

            result = {
                "action": action,
                "total_requested": len(driver_ids),
                "successful_updates": len([d for d in updated_drivers if d.get("changed", False)]),
                "no_change_needed": len([d for d in updated_drivers if not d.get("changed", True)]),
                "failed_updates": len(failed_drivers),
                "updated_drivers": updated_drivers,
                "failed_drivers": failed_drivers
            }

            logger.info(f"📊 Bulk update completed:")
            logger.info(f"   • Successful: {result['successful_updates']}")
            logger.info(f"   • No change needed: {result['no_change_needed']}")
            logger.info(f"   • Failed: {result['failed_updates']}")

            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during bulk driver update: {str(e)}")
            db.rollback()
            raise ValueError(f"Database error during bulk update: {str(e)}") from e

    @staticmethod
    def search_drivers(db: Session, filters: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search drivers with filters for admin dashboard"""
        logger.info(f"🔍 ===== ADMIN DRIVER SEARCH =====")
        logger.info(f"📋 Filters: {filters}")
        logger.info(f"🔢 Limit: {limit}")

        try:
            query = db.query(Driver)

            # Apply filters
            if filters.get("is_available") is not None:
                query = query.filter(Driver.is_available == filters["is_available"])
                logger.debug(f"🔍 Filtering by availability: {filters['is_available']}")

            # Add more filters based on your Driver model fields
            # if filters.get("vehicle_type"):
            #     query = query.filter(Driver.vehicle_type == filters["vehicle_type"])
            
            # if filters.get("email"):
            #     query = query.filter(Driver.email.ilike(f"%{filters['email']}%"))

            # if filters.get("phone"):
            #     query = query.filter(Driver.phone.ilike(f"%{filters['phone']}%"))

            # Order by driver_id or creation date
            query = query.order_by(Driver.driver_id)

            drivers = query.limit(limit).all()
            
            # Format response
            result = []
            for driver in drivers:
                driver_info = {
                    "driver_id": driver.driver_id,
                    "is_available": driver.is_available,
                    "status": "available" if driver.is_available else "unavailable"
                    # Add more fields as needed:
                    # "name": getattr(driver, 'name', None),
                    # "email": getattr(driver, 'email', None),
                    # "phone": getattr(driver, 'phone', None),
                    # "vehicle_type": getattr(driver, 'vehicle_type', None),
                    # "created_at": getattr(driver, 'created_at', None)
                }
                result.append(driver_info)

            logger.info(f"✅ Found {len(result)} drivers matching criteria")
            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error during driver search: {str(e)}")
            raise ValueError(f"Error searching drivers: {str(e)}") from e

    @staticmethod
    def get_driver_orders_summary(db: Session, driver_id: str, days: int = 30) -> Dict[str, Any]:
        """Get orders summary for a specific driver"""
        logger.info(f"📋 ===== DRIVER ORDERS SUMMARY =====")
        logger.info(f"🚗 Driver ID: {driver_id}")
        logger.info(f"📅 Period: {days} days")

        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # Verify driver exists
            driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
            if not driver:
                logger.error(f"❌ Driver not found: {driver_id}")
                raise ValueError(f"Driver with ID {driver_id} not found")

            # Get recent orders
            recent_orders = db.query(Order)\
                .filter(Order.driver_id == driver_id)\
                .filter(Order.created_at >= cutoff_date)\
                .order_by(Order.created_at.desc())\
                .limit(20)\
                .all()

            # Format orders for response
            orders_summary = []
            for order in recent_orders:
                order_info = {
                    "order_id": order.id,
                    "status": order.status.value,
                    "price": float(order.price),
                    "distance_km": float(order.distance_km) if order.distance_km else 0,
                    "created_at": order.created_at.isoformat(),
                    "pickup_address": order.pickup_address,
                    "dropoff_address": order.dropoff_address,
                    "order_type": order.order_type
                }
                orders_summary.append(order_info)

            # Calculate quick stats
            total_orders = len(recent_orders)
            total_earnings = sum(float(o.price) for o in recent_orders if o.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED])

            summary = {
                "driver_id": driver_id,
                "period_days": days,
                "total_recent_orders": total_orders,
                "total_earnings": total_earnings,
                "current_availability": driver.is_available,
                "recent_orders": orders_summary
            }

            logger.info(f"📋 Orders summary generated:")
            logger.info(f"   • Recent orders: {total_orders}")
            logger.info(f"   • Total earnings: R{total_earnings}")

            return summary

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating driver orders summary: {str(e)}")
            raise ValueError(f"Error generating driver orders summary: {str(e)}") from e

    @staticmethod
    def admin_create_driver_report(db: Session, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive driver report for admin"""
        logger.info(f"📊 ===== GENERATING DRIVER REPORT ({days} days) =====")

        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # Get all drivers
            all_drivers = db.query(Driver).all()
            total_drivers = len(all_drivers)
            active_drivers = sum(1 for d in all_drivers if d.is_available)

            # Get orders in period with driver assignments
            orders_with_drivers = db.query(Order)\
                .filter(Order.driver_id.isnot(None))\
                .filter(Order.created_at >= cutoff_date)\
                .all()

            # Driver performance metrics
            driver_metrics = {}
            for order in orders_with_drivers:
                driver_id = order.driver_id
                if driver_id not in driver_metrics:
                    driver_metrics[driver_id] = {
                        "total_orders": 0,
                        "completed_orders": 0,
                        "total_earnings": Decimal("0"),
                        "total_distance": Decimal("0")
                    }
                
                driver_metrics[driver_id]["total_orders"] += 1
                if order.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED]:
                    driver_metrics[driver_id]["completed_orders"] += 1
                    driver_metrics[driver_id]["total_earnings"] += order.price
                
                if order.distance_km:
                    driver_metrics[driver_id]["total_distance"] += order.distance_km

            # Top performing drivers
            top_drivers = sorted(
                [(driver_id, metrics) for driver_id, metrics in driver_metrics.items()],
                key=lambda x: x[1]["total_earnings"],
                reverse=True
            )[:10]

            # Format top drivers for response
            top_drivers_formatted = []
            for driver_id, metrics in top_drivers:
                completion_rate = (metrics["completed_orders"] / metrics["total_orders"] * 100) if metrics["total_orders"] > 0 else 0
                top_drivers_formatted.append({
                    "driver_id": driver_id,
                    "total_orders": metrics["total_orders"],
                    "completed_orders": metrics["completed_orders"],
                    "completion_rate": round(completion_rate, 2),
                    "total_earnings": float(metrics["total_earnings"]),
                    "total_distance_km": float(metrics["total_distance"])
                })

            report = {
                "period_days": days,
                "period_start": cutoff_date.date().isoformat(),
                "period_end": datetime.now().date().isoformat(),
                "total_drivers": total_drivers,
                "active_drivers": active_drivers,
                "inactive_drivers": total_drivers - active_drivers,
                "drivers_with_orders": len(driver_metrics),
                "total_orders_assigned": len(orders_with_drivers),
                "top_performing_drivers": top_drivers_formatted,
                "average_orders_per_active_driver": len(orders_with_drivers) / len(driver_metrics) if driver_metrics else 0
            }

            logger.info(f"📊 Driver report generated:")
            logger.info(f"   • Total drivers: {total_drivers}")
            logger.info(f"   • Active: {active_drivers}")
            logger.info(f"   • Orders assigned: {len(orders_with_drivers)}")

            return report

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error generating driver report: {str(e)}")
            raise ValueError(f"Error generating driver report: {str(e)}") from e
