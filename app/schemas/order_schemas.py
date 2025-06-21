from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models.order_models import OrderType, OrderStatus

class OrderCreate(BaseModel):
    order_type: OrderType
    pickup_address: str
    pickup_latitude: str
    pickup_longitude: str
    dropoff_address: str
    dropoff_latitude: str
    dropoff_longitude: str
    client_id: str
    special_instructions: Optional[str] = None
    patient_details: Optional[str] = None
    medical_items: Optional[str] = None

class AdminOrderCreate(OrderCreate):
    client_id: str

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
    
    model_config = {"from_attributes": True}

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderAccept(BaseModel):
    driver_id: str
    estimated_price: Decimal
