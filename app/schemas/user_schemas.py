from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CLIENT = "client"
    DRIVER = "driver"

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str

class UserResponse(UserBase):
    id: str
    role: Optional[UserRole] = None # Added role field
    created_at: datetime
    
    model_config = {"from_attributes": True}

class ClientCreate(BaseModel):
    home_address: Optional[str] = None

class ClientResponse(BaseModel):
    client_id: str
    home_address: Optional[str] = None
    is_verified: bool
    user: UserResponse
    
    model_config = {"from_attributes": True}

class DriverCreate(BaseModel):
    license_no: Optional[str] = None
    vehicle_type: Optional[str] = None

class DriverResponse(BaseModel):
    driver_id: str
    license_no: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_available: bool
    user: UserResponse
    
    model_config = {"from_attributes": True}

class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    license_no: Optional[str] = None
    vehicle_type: Optional[str] = None
    # is_available is removed from here and will have its own update schema and endpoint

class DriverAvailabilityUpdate(BaseModel):
    is_available: bool

class DriverLocationResponse(BaseModel):
    driver_id: str
    latitude: float
    longitude: float
    # timestamp: Optional[datetime] = None # Optional: if you decide to store and return it from Redis
