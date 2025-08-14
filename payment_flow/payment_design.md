# Payment Management System Design

## Database Models

### Payment Model

```python
from sqlalchemy import Column, String, DateTime, Numeric, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from ..database import Base

class PaymentType(PyEnum):
    CLIENT_PAYMENT = "client_payment"
    DRIVER_PAYMENT = "driver_payment"

class PaymentStatus(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"

class PaymentMethod(PyEnum):
    CREDIT_CARD = "credit_card"
    MOBILE_MONEY = "mobile_money"
    CASH = "cash"
    OTHER = "other"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    user_id = Column(String, nullable=False)  # Can be client_id or driver_id
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="ZAR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)  # External transaction ID
    transaction_details = Column(Text, nullable=True)  # JSON string for additional details
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="payments")
```

### Refund Model

```python
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
```

### Order Model Updates

```python
# Add to existing Order model
class Order(Base):
    # ... existing fields ...

    # Add payment status tracking
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_paid = Column(Numeric(10, 2), default=0.00)
    total_refunded = Column(Numeric(10, 2), default=0.00)

    # Relationships
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
```

## Key Features

1. **Flexible Payment Methods**: Supports credit card, mobile money, cash, and other methods
2. **Dual Payment Tracking**: Tracks both client payments (to platform) and driver payments (from platform)
3. **Payment Status Integration**: Integrates with order status workflow
4. **Partial Payments**: Supports partial payments and refunds
5. **Transaction Details**: Stores external transaction IDs and additional details for audit
6. **Currency Support**: Defaults to ZAR but can be extended for multi-currency
7. **Relationship Management**: Proper relationships between orders, payments, and refunds