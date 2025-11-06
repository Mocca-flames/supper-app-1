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
    client_id = Column(String, ForeignKey("users.id"), nullable=False)
    request_id = Column(String, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=False)  # e.g., 'Credit Card', 'Cash', 'Transfer'
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)  # External payment gateway transaction ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("User", back_populates="payments")
    request = relationship("Order", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment")

class PayoutStatus(enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    FAILED = "failed"

class DriverPayout(Base):
    __tablename__ = "driver_payouts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id = Column(String, ForeignKey("users.id"), nullable=False)
    request_id = Column(String, ForeignKey("orders.id"), nullable=False)
    payout_amount = Column(Numeric(10, 2), nullable=False)
    payout_date = Column(DateTime, nullable=True)
    payout_status = Column(Enum(PayoutStatus), default=PayoutStatus.REQUESTED)
    payment_request_ref = Column(String, nullable=True)
    disbursement_method = Column(String, nullable=True)  # e.g., 'Bank Transfer', 'Wallet'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    driver = relationship("User", back_populates="driver_payouts")
    request = relationship("Order", back_populates="driver_payouts")

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
