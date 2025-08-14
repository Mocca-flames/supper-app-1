from pydantic import BaseModel
from typing import Optional, List
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