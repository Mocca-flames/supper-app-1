# Order Model Updates for Payment Integration

## Updated Order Model

```python
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..database import Base
from ..models.payment_models import PaymentStatus

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("users.id"), nullable=False)
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
    patient_details = Column(Text, nullable=True)
    medical_items = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Payment integration fields
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_paid = Column(Numeric(10, 2), default=0.00)
    total_refunded = Column(Numeric(10, 2), default=0.00)

    # Relationships
    user = relationship("User", foreign_keys=[client_id], back_populates="orders")
    driver = relationship("Driver", back_populates="orders")

    # Payment relationships
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
```

## Updated Order Response Schema

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from ..models.order_models import OrderType, OrderStatus
from ..models.payment_models import PaymentStatus
from .payment_schemas import PaymentResponse, RefundResponse

class OrderResponse(BaseModel):
    id: str
    client_id: str
    driver_id: Optional[str] = None
    order_type: OrderType
    status: OrderStatus
    pickup_address: str
    pickup_latitude: Optional[str] = None
    pickup_longitude: Optional[str] = None
    dropoff_address: str
    dropoff_latitude: Optional[str] = None
    dropoff_longitude: Optional[str] = None
    price: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    special_instructions: Optional[str] = None
    created_at: datetime

    # Payment integration fields
    payment_status: PaymentStatus
    total_paid: Decimal
    total_refunded: Decimal
    payments: Optional[List[PaymentResponse]] = []
    refunds: Optional[List[RefundResponse]] = []

    model_config = {"from_attributes": True}
```

## Key Changes

1. **Payment Status Tracking**: Added `payment_status` field to track overall payment status
2. **Payment Totals**: Added `total_paid` and `total_refunded` to track amounts
3. **Relationships**: Added relationships to Payment and Refund models
4. **Schema Updates**: Updated OrderResponse to include payment information
5. **Integration**: Payment status is now part of the order lifecycle