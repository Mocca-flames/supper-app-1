from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import uuid
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Firebase UID
    email = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    role = Column(String, nullable=True)  # Added role attribute (e.g., "client", "driver")
    fcm_token = Column(String, nullable=True)  # FCM token for push notifications
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client_profile = relationship("Client", back_populates="user", uselist=False)
    driver_profile = relationship("Driver", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user", foreign_keys="[Order.client_id]") # Added orders relationship
    payments = relationship("Payment", back_populates="client")
    driver_payouts = relationship("DriverPayout", back_populates="driver")

class Client(Base):
    __tablename__ = "clients"

    client_id = Column(String, ForeignKey("users.id", onupdate="CASCADE"), primary_key=True)
    home_address = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="client_profile")
  

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, ForeignKey("users.id", onupdate="CASCADE"), primary_key=True)
    license_no = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)  # 'car', 'bike', 'ambulance', 'van'
    is_available = Column(Boolean, default=True)
    current_latitude = Column(String, nullable=True)
    current_longitude = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="driver_profile")
    orders = relationship("Order", back_populates="driver")

