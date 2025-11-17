from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from ..models.payment_models import PaymentType, PaymentStatus, PaymentMethod, PaymentGateway, PayoutStatus

class PaymentCreate(BaseModel):
    client_id: str
    request_id: str
    amount: Decimal
    payment_method: str
    payment_type: PaymentType
    currency: str
    gateway: Optional[PaymentGateway] = None
    transaction_id: Optional[str] = None

class PaymentResponse(BaseModel):
    id: str
    client_id: str
    request_id: str
    amount: Decimal
    payment_date: Optional[datetime] = None
    payment_method: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    payment_date: Optional[datetime] = None

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

class DriverPayoutCreate(BaseModel):
    driver_id: str
    request_id: str
    payout_amount: Decimal

class DriverPayoutResponse(BaseModel):
    id: str
    driver_id: str
    request_id: str
    payout_amount: Decimal
    payout_date: Optional[datetime] = None
    payout_status: PayoutStatus
    payment_request_ref: Optional[str] = None
    disbursement_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class DriverPayoutUpdate(BaseModel):
    payout_status: Optional[PayoutStatus] = None
    payout_date: Optional[datetime] = None
    disbursement_method: Optional[str] = None

class RevenueReport(BaseModel):
    gross_revenue: Decimal
    total_payouts: Decimal
    net_profit: Decimal
    period_start: datetime
    period_end: datetime

class ProfitReport(BaseModel):
    gross_revenue: Decimal
    total_payouts: Decimal
    net_profit: Decimal
    period_start: datetime
    period_end: datetime

class LedgerEntry(BaseModel):
    date: datetime
    type: str  # 'payment' or 'payout'
    amount: Decimal
    description: str
    reference_id: str

class HistoryReport(BaseModel):
    entries: List[LedgerEntry]
    period_start: datetime
    period_end: datetime