from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..database import Base
from ..models.payment_models import PaymentStatus

class OrderType(enum.Enum):
    RIDE = "ride"
    FOOD_DELIVERY = "food_delivery"
    PARCEL_DELIVERY = "parcel_delivery"
    MEDICAL_PRODUCT = "medical_product"
    PATIENT_TRANSPORT = "patient_transport"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("users.id"), nullable=False)  # Changed ForeignKey to users.id
    driver_id = Column(String, ForeignKey("drivers.driver_id"), nullable=True)

    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

    pickup_address = Column(Text, nullable=False)
    pickup_latitude = Column(String, nullable=True)
    pickup_longitude = Column(String, nullable=True)

    dropoff_address = Column(Text, nullable=False)
    dropoff_latitude = Column(String, nullable=True)
    dropoff_longitude = Column(String, nullable=True)

    price = Column(Numeric(10, 2), nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)

    special_instructions = Column(Text, nullable=True)
    patient_details = Column(Text, nullable=True)  # For patient transport
    medical_items = Column(Text, nullable=True)    # For medical delivery

    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Payment integration fields
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_paid = Column(Numeric(10, 2), default=0.00)
    total_refunded = Column(Numeric(10, 2), default=0.00)

    # Relationships
    user = relationship("User", foreign_keys=[client_id], back_populates="orders") # Changed relationship to User
    driver = relationship("Driver", back_populates="orders")

    # Payment relationships
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
