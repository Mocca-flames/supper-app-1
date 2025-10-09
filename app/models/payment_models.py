from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..database import Base

class PaymentType(enum.Enum):
    CLIENT_PAYMENT = "client_payment"
    DRIVER_PAYMENT = "driver_payment"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"

class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    MOBILE_MONEY = "mobile_money"
    CASH = "cash"
    OTHER = "other"

class PaymentGateway(enum.Enum):
    PAYFAST = "payfast"
    PAYSTACK = "paystack"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    user_id = Column(String, nullable=False)  # Can be client_id or driver_id
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="ZAR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    gateway = Column(Enum(PaymentGateway), nullable=False, default=PaymentGateway.PAYFAST)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)  # External transaction ID
    transaction_details = Column(Text, nullable=True)  # JSON string for additional details
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String, ForeignKey("payments.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    order = relationship("Order", back_populates="refunds")
