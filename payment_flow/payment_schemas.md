# Payment Schemas Design

## Payment Schemas

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models.payment_models import PaymentType, PaymentStatus, PaymentMethod

class PaymentCreate(BaseModel):
    order_id: str
    user_id: str
    payment_type: PaymentType
    amount: Decimal
    currency: str = "ZAR"
    payment_method: PaymentMethod
    transaction_id: Optional[str] = None
    transaction_details: Optional[dict] = None

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    user_id: str
    payment_type: PaymentType
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    transaction_details: Optional[dict] = None

class RefundCreate(BaseModel):
    payment_id: str
    order_id: str
    amount: Decimal
    reason: Optional[str] = None

class RefundResponse(BaseModel):
    id: str
    payment_id: str
    order_id: str
    amount: Decimal
    reason: Optional[str] = None
    status: PaymentStatus
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
```

## Order Schema Updates

```python
# Add to existing OrderResponse schema
class OrderResponse(BaseModel):
    # ... existing fields ...
    payment_status: PaymentStatus
    total_paid: Decimal
    total_refunded: Decimal
    payments: Optional[List[PaymentResponse]] = []
    refunds: Optional[List[RefundResponse]] = []
```

## Key Features

1. **Type Safety**: Uses Pydantic for validation and type safety
2. **Flexible Payment Methods**: Supports all defined payment methods
3. **Status Tracking**: Full payment lifecycle status tracking
4. **Transaction Details**: Supports storing external transaction references
5. **Currency Support**: Defaults to ZAR but can be extended
6. **Order Integration**: Payment and refund information included in order responses