from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from ..models.order_models import OrderType, OrderStatus
from ..models.payment_models import PaymentStatus

class OrderCreate(BaseModel):
    order_type: OrderType
    pickup_address: str
    pickup_latitude: str
    pickup_longitude: str
    dropoff_address: str
    dropoff_latitude: str
    dropoff_longitude: str
    client_id: str
    distance_km: str # Added distance_km as string from frontend
    special_instructions: Optional[str] = None
    patient_details: Optional[str] = None
    medical_items: Optional[str] = None

class AdminOrderCreate(OrderCreate):
    client_id: str

class InHouseOrderCreate(BaseModel):
    order_type: OrderType
    pickup_address: str
    pickup_latitude: str
    pickup_longitude: str
    dropoff_address: str
    dropoff_latitude: str
    dropoff_longitude: str
    distance_km: str
    total_paid: Decimal
    payment_status: PaymentStatus
    special_instructions: Optional[str] = None
    patient_details: Optional[str] = None
    medical_items: Optional[str] = None

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
    payment_status: PaymentStatus
    total_paid: Optional[Decimal] = None
    total_refunded: Optional[Decimal] = None

    model_config = {"from_attributes": True}

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderAccept(BaseModel):
    driver_id: str
    estimated_price: Optional[Decimal] = None

class TrackingSessionResponse(BaseModel):
    session_id: str
    order_id: str
    status: str  # e.g., "active", "pending_driver_acceptance"
    message: Optional[str] = None
    # Potentially add driver_id, current_location if available at session start

class OrderUpdate(BaseModel):
    payment_status: Optional[PaymentStatus] = None
class OrderEstimateRequest(BaseModel):
    service_type: str  # "rideshare", "medical_transport", "food_delivery", "product_delivery"
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    passenger_count: Optional[int] = None
    vehicle_type: Optional[str] = None
    mobility_needs: Optional[List[str]] = None
    transport_type: Optional[str] = None
    package_size: Optional[str] = None
    delivery_time_preference: Optional[str] = None

class EstimateDetails(BaseModel):
    base_fare: float
    distance_fare: float
    service_fee: float
    total: float
    estimated_duration_minutes: int
    currency: str
    surge_multiplier: float
    medical_surcharge: float
    package_surcharge: float
    delivery_fee: float

class CostEstimationResponse(BaseModel):
    estimate: EstimateDetails
    valid_until: str  # ISO 8601 datetime string
    special_instructions: Optional[str] = None
