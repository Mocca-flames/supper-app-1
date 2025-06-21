# Supper Delivery System - Complete Development Guide

## Project Structure
```
supper_delivery/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── firebase_auth.py   # Firebase authentication
│   │   └── middleware.py      # Auth middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_models.py     # User, Client, Driver models
│   │   ├── order_models.py    # Order/Delivery models
│   │   └── discount_models.py # Partner discount models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user_schemas.py    # Pydantic schemas for users
│   │   ├── order_schemas.py   # Pydantic schemas for orders
│   │   └── discount_schemas.py # Pydantic schemas for discounts
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py    # User business logic
│   │   ├── order_service.py   # Order business logic
│   │   ├── driver_service.py  # Driver business logic
│   │   └── websocket_service.py # Real-time updates
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth_routes.py     # Authentication endpoints
│   │   ├── client_routes.py   # Client endpoints
│   │   ├── driver_routes.py   # Driver endpoints
│   │   ├── admin_routes.py    # Admin endpoints
│   │   └── websocket_routes.py # WebSocket endpoints
│   └── utils/
│       ├── __init__.py
│       ├── redis_client.py    # Redis connection
│       └── helpers.py         # Utility functions
├── tests/
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Step-by-Step Development Guide

### Phase 1: Environment Setup (Day 1)

#### 1.1 Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 1.2 Install Dependencies
Create `requirements.txt`:
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
redis==5.0.1
firebase-admin==6.2.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
websockets==12.0
```

#### 1.3 Setup Database (PostgreSQL)
```bash
# Use Docker
docker run --name supper-postgres -e POSTGRES_PASSWORD=Maurice -p 5432:5432 -d postgres
```

#### 1.4 Setup Redis
```bash
# Use Docker
docker run --name supper-redis -p 6379:6379 -d redis
```

### Phase 2: Core Configuration (Day 1-2)

#### 2.1 Create `app/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:your_password@localhost/supper_delivery"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"
    FIREBASE_CREDENTIALS_PATH: str = "path/to/firebase-credentials.json"
    
    # App Settings
    SECRET_KEY: str = "your-secret-key-here"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 2.2 Create `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 2.3 Create `app/utils/redis_client.py`
```python
import redis
from .config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RedisService:
    @staticmethod
    def set_driver_location(driver_id: str, latitude: float, longitude: float):
        redis_client.hset(
            f"driver_location:{driver_id}",
            mapping={"lat": latitude, "lng": longitude}
        )
    
    @staticmethod
    def get_driver_location(driver_id: str):
        return redis_client.hgetall(f"driver_location:{driver_id}")
    
    @staticmethod
    def set_order_status(order_id: str, status: str):
        redis_client.set(f"order_status:{order_id}", status)
    
    @staticmethod
    def get_order_status(order_id: str):
        return redis_client.get(f"order_status:{order_id}")
```

### Phase 3: Database Models (Day 2-3)

#### 3.1 Create `app/models/user_models.py`
```python
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Firebase UID
    email = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client_profile = relationship("Client", back_populates="user", uselist=False)
    driver_profile = relationship("Driver", back_populates="user", uselist=False)

class Client(Base):
    __tablename__ = "clients"
    
    client_id = Column(String, ForeignKey("users.id"), primary_key=True)
    home_address = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="client_profile")
    orders = relationship("Order", back_populates="client")

class Driver(Base):
    __tablename__ = "drivers"
    
    driver_id = Column(String, ForeignKey("users.id"), primary_key=True)
    approved = Column(Boolean, default=False)
    license_no = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)  # 'car', 'bike', 'ambulance', 'van'
    is_available = Column(Boolean, default=True)
    current_latitude = Column(String, nullable=True)
    current_longitude = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="driver_profile")
    orders = relationship("Order", back_populates="driver")
```

#### 3.2 Create `app/models/order_models.py`
```python
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..database import Base

class OrderType(enum.Enum):
    RIDE = "ride"
    FOOD_DELIVERY = "food_delivery"
    PARCEL_DELIVERY = "parcel_delivery"
    MEDICAL_PRODUCT = "medical_product"
    PATIENT_TRANSPORT = "patient_transport"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("clients.client_id"), nullable=False)
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
    patient_details = Column(Text, nullable=True)  # For patient transport
    medical_items = Column(Text, nullable=True)    # For medical delivery
    
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client", back_populates="orders")
    driver = relationship("Driver", back_populates="orders")
```

#### 3.3 Create `app/models/discount_models.py`
```python
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from ..database import Base

class PartnerDiscount(Base):
    __tablename__ = "partner_discounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # Company/Event name
    discount_percent = Column(Integer, nullable=False)  # 30 = 30%
    condition_text = Column(Text, nullable=True)  # "to location = Event B"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Phase 4: Pydantic Schemas (Day 3-4)

#### 4.1 Create `app/schemas/user_schemas.py`
```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    firebase_uid: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    home_address: Optional[str] = None

class ClientResponse(BaseModel):
    client_id: str
    home_address: Optional[str] = None
    is_verified: bool
    user: UserResponse
    
    class Config:
        from_attributes = True

class DriverCreate(BaseModel):
    license_no: Optional[str] = None
    vehicle_type: Optional[str] = None

class DriverResponse(BaseModel):
    driver_id: str
    approved: bool
    license_no: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_available: bool
    user: UserResponse
    
    class Config:
        from_attributes = True

class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float
```

#### 4.2 Create `app/schemas/order_schemas.py`
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from ..models.order_models import OrderType, OrderStatus

class OrderCreate(BaseModel):
    order_type: OrderType
    pickup_address: str
    pickup_latitude: Optional[str] = None
    pickup_longitude: Optional[str] = None
    dropoff_address: str
    dropoff_latitude: Optional[str] = None
    dropoff_longitude: Optional[str] = None
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
    dropoff_address: str
    price: Optional[Decimal] = None
    distance_km: Optional[Decimal] = None
    special_instructions: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderAccept(BaseModel):
    driver_id: str
    estimated_price: Decimal
```

### Phase 5: Authentication System (Day 4-5)

#### 5.1 Create `app/auth/firebase_auth.py`
```python
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException
from ..config import settings

# Initialize Firebase Admin SDK
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)

class FirebaseAuth:
    @staticmethod
    def verify_firebase_token(token: str) -> str:
        """Verify Firebase token and return user ID"""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token["uid"]
        except Exception as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid Firebase token: {str(e)}"
            )
    
    @staticmethod
    def get_user_info(uid: str):
        """Get user info from Firebase"""
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "phone_number": user.phone_number,
                "display_name": user.display_name
            }
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"User not found: {str(e)}"
            )
```

#### 5.2 Create `app/auth/middleware.py`
```python
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from .firebase_auth import FirebaseAuth
from ..database import get_db
from ..models.user_models import User

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Expected format: "Bearer <token>"
        token = authorization.split(" ")[1]
        firebase_uid = FirebaseAuth.verify_firebase_token(token)
        
        # Get user from database
        user = db.query(User).filter(User.id == firebase_uid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")
        
        return user
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

def get_current_client(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current client profile"""
    if not current_user.client_profile:
        raise HTTPException(status_code=403, detail="Client profile not found")
    return current_user.client_profile

def get_current_driver(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current driver profile"""
    if not current_user.driver_profile:
        raise HTTPException(status_code=403, detail="Driver profile not found")
    return current_user.driver_profile

def get_approved_driver(
    current_driver = Depends(get_current_driver)
):
    """Get current approved driver"""
    if not current_driver.approved:
        raise HTTPException(status_code=403, detail="Driver not approved")
    return current_driver
```

### Phase 6: Service Layer (Day 5-6)

#### 6.1 Create `app/services/user_service.py`
```python
from sqlalchemy.orm import Session
from ..models.user_models import User, Client, Driver
from ..schemas.user_schemas import UserCreate, ClientCreate, DriverCreate
from ..auth.firebase_auth import FirebaseAuth

class UserService:
    @staticmethod
    def create_user_from_firebase(db: Session, firebase_uid: str) -> User:
        # Get user info from Firebase
        firebase_user = FirebaseAuth.get_user_info(firebase_uid)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.id == firebase_uid).first()
        if existing_user:
            return existing_user
        
        # Create new user
        user = User(
            id=firebase_uid,
            email=firebase_user.get("email"),
            full_name=firebase_user.get("display_name"),
            phone_number=firebase_user.get("phone_number")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_client_profile(db: Session, user_id: str, client_data: ClientCreate) -> Client:
        client = Client(
            client_id=user_id,
            home_address=client_data.home_address
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    
    @staticmethod
    def create_driver_profile(db: Session, user_id: str, driver_data: DriverCreate) -> Driver:
        driver = Driver(
            driver_id=user_id,
            license_no=driver_data.license_no,
            vehicle_type=driver_data.vehicle_type
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        return driver
    
    @staticmethod
    def get_pending_drivers(db: Session):
        return db.query(Driver).filter(Driver.approved == False).all()
    
    @staticmethod
    def approve_driver(db: Session, driver_id: str) -> Driver:
        driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
        if not driver:
            raise ValueError("Driver not found")
        
        driver.approved = True
        db.commit()
        db.refresh(driver)
        return driver
```

#### 6.2 Create `app/services/order_service.py`
```python
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from ..models.order_models import Order, OrderStatus
from ..schemas.order_schemas import OrderCreate, OrderAccept
from ..utils.redis_client import RedisService

class OrderService:
    @staticmethod
    def create_order(db: Session, client_id: str, order_data: OrderCreate) -> Order:
        order = Order(
            client_id=client_id,
            order_type=order_data.order_type,
            pickup_address=order_data.pickup_address,
            pickup_latitude=order_data.pickup_latitude,
            pickup_longitude=order_data.pickup_longitude,
            dropoff_address=order_data.dropoff_address,
            dropoff_latitude=order_data.dropoff_latitude,
            dropoff_longitude=order_data.dropoff_longitude,
            special_instructions=order_data.special_instructions,
            patient_details=order_data.patient_details,
            medical_items=order_data.medical_items
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Cache order status in Redis
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def get_pending_orders(db: Session) -> List[Order]:
        return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
    
    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError("Order already accepted or completed")
        
        order.driver_id = accept_data.driver_id
        order.status = OrderStatus.ACCEPTED
        order.price = accept_data.estimated_price
        
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        order.status = new_status
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def get_client_orders(db: Session, client_id: str) -> List[Order]:
        return db.query(Order).filter(Order.client_id == client_id).all()
    
    @staticmethod
    def get_driver_orders(db: Session, driver_id: str) -> List[Order]:
        return db.query(Order).filter(Order.driver_id == driver_id).all()
```

### Phase 7: API Routes (Day 6-8)

#### 7.1 Create `app/api/auth_routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schemas import UserResponse, ClientCreate, ClientResponse, DriverCreate, DriverResponse
from ..auth.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register_user(
    firebase_uid: str,
    db: Session = Depends(get_db)
):
    """Register a new user from Firebase UID"""
    user = UserService.create_user_from_firebase(db, firebase_uid)
    return user

@router.post("/client-profile", response_model=ClientResponse)
def create_client_profile(
    client_data: ClientCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create client profile for current user"""
    if current_user.client_profile:
        raise HTTPException(status_code=400, detail="Client profile already exists")
    
    client = UserService.create_client_profile(db, current_user.id, client_data)
    return client

@router.post("/driver-profile", response_model=DriverResponse)
def create_driver_profile(
    driver_data: DriverCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create driver profile for current user"""
    if current_user.driver_profile:
        raise HTTPException(status_code=400, detail="Driver profile already exists")
    
    driver = UserService.create_driver_profile(db, current_user.id, driver_data)
    return driver

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    return current_user
```

#### 7.2 Create `app/api/client_routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.order_service import OrderService
from ..schemas.order_schemas import OrderCreate, OrderResponse
from ..auth.middleware import get_current_client

router = APIRouter(prefix="/client", tags=["Client"])

@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    current_client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Create a new order/ride request"""
    order = OrderService.create_order(db, current_client.client_id, order_data)
    return order

@router.get("/orders", response_model=List[OrderResponse])
def get_my_orders(
    current_client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get all orders for current client"""
    orders = OrderService.get_client_orders(db, current_client.client_id)
    return orders

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_details(
    order_id: str,
    current_client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Get specific order details"""
    orders = OrderService.get_client_orders(db, current_client.client_id)
    order = next((o for o in orders if o.id == order_id), None)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order
```

#### 7.3 Create `app/api/driver_routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.order_service import OrderService
from ..schemas.order_schemas import OrderResponse, OrderAccept, OrderStatusUpdate
from ..schemas.user_schemas import DriverLocationUpdate
from ..auth.middleware import get_approved_driver
from ..utils.redis_client import RedisService

router = APIRouter(prefix="/driver", tags=["Driver"])

@router.get("/available-orders", response_model=List[OrderResponse])
def get_available_orders(
    current_driver = Depends(get_approved_driver),
    db: Session = Depends(get_db)
):
    """Get all pending orders for drivers"""
    orders = OrderService.get_pending_orders(db)
    return orders

@router.post("/accept-order/{order_id}", response_model=OrderResponse)
def accept_order(
    order_id: str,
    accept_data: OrderAccept,
    current_driver = Depends(get_approved_driver),
    db: Session = Depends(get_db)
):
    """Accept an order"""
    # Ensure driver is accepting for themselves
    if accept_data.driver_id != current_driver.driver_id:
        raise HTTPException(status_code=403, detail="Cannot accept order for another driver")
    
    order = OrderService.accept_order(db, order_id, accept_data)
    return order

@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    current_driver = Depends(get_approved_driver),
    db: Session = Depends(get_db)
):
    """Get all orders for current driver"""
    orders = OrderService.get_driver_orders(db, current_driver.driver_id)
    return orders

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    current_driver = Depends(get_approved_driver),
    db: Session = Depends(get_db)
):
    """Update order status"""
    order = OrderService.update_order_status(db, order_id, status_data.status)
    
    # Verify driver owns this order
    if order.driver_id != current_driver.driver_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this order")
    
    return order

@router.post("/location")
def update_location(
    location_data: DriverLocationUpdate,
    current_driver = Depends(get_approved_driver)
):
    """Update driver location"""
    RedisService.set_driver_location(
        current_driver.driver_id,
        location_data.latitude,
        location_data.longitude
    )
    return {"message": "Location updated successfully"}
```

#### 7.4 Create `app/api/admin_routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user_schemas import DriverResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

# Simple admin authentication - in production, implement proper admin roles
def verify_admin_key(admin_key: str = None):
    if admin_key != "admin_secret_key_123":  # Change this!
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

@router.get("/drivers/pending", response_model=List[DriverResponse])
def get_pending_drivers(
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Get all pending driver approvals"""
    drivers = UserService.get_pending_drivers(db)
    return drivers

@router.post("/drivers/{driver_id}/approve", response_model=DriverResponse)
def approve_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    admin_verified = Depends(verify_admin_key)
):
    """Approve a driver"""
    try:
        driver = UserService.approve_driver(db, driver_id)
        return driver
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

### Phase 8: WebSocket Implementation (Day 8-9)

#### 8.1 Create `app/services/websocket_service.py`
```python
from fastapi import WebSocket
from typing import Dict, List
import json
from ..utils.redis_client import RedisService

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connections by order_id for order tracking
        self.order_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)
    
    async def send_order_update(self, order_id: str, message: dict):
        """Send update to all users tracking this order"""
        if order_id in self.order_connections:
            for user_id in self.order_connections[order_id]:
                await self.send_personal_message(json.dumps(message), user_id)
    
    def subscribe_to_order(self, order_id: str, user_id: str):
        """Subscribe user to order updates"""
        if order_id not in self.order_connections:
            self.order_connections[order_id] = []
        if user_id not in self.order_connections[order_id]:
            self.order_connections[order_id].append(user_id)
    
    def unsubscribe_from_order(self, order_id: str, user_id: str):
        """Unsubscribe user from order updates"""
        if order_id in self.order_connections:
            if user_id in self.order_connections[order_id]:
                self.order_connections[order_id].remove(user_id)

# Global connection manager instance
connection_manager = ConnectionManager()

class WebSocketService:
    @staticmethod
    async def broadcast_order_status_update(order_id: str, status: str, driver_location: dict = None):
        """Broadcast order status update to subscribed users"""
        message = {
            "type": "order_status_update",
            "order_id": order_id,
            "status": status,
            "timestamp": str(datetime.utcnow())
        }
        
        if driver_location:
            message["driver_location"] = driver_location
        
        await connection_manager.send_order_update(order_id, message)
    
    @staticmethod
    async def broadcast_driver_location(driver_id: str, latitude: float, longitude: float):
        """Broadcast driver location to relevant orders"""
        location_data = {
            "type": "driver_location_update",
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": str(datetime.utcnow())
        }
        
        # Store in Redis
        RedisService.set_driver_location(driver_id, latitude, longitude)
        
        # Send to all active orders for this driver
        # Note: You'll need to implement logic to find active orders for driver
        # For now, we'll store it in Redis and let the frontend pull it
```

#### 8.2 Create `app/api/websocket_routes.py`
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.websocket_service import connection_manager, WebSocketService
from ..auth.firebase_auth import FirebaseAuth
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_order":
                order_id = message.get("order_id")
                connection_manager.subscribe_to_order(order_id, user_id)
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "order_id": order_id
                }))
            
            elif message.get("type") == "driver_location_update":
                # Handle driver location updates
                latitude = message.get("latitude")
                longitude = message.get("longitude")
                await WebSocketService.broadcast_driver_location(user_id, latitude, longitude)
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)

@router.websocket("/ws/track/{order_id}")
async def track_order_websocket(websocket: WebSocket, order_id: str):
    await websocket.accept()
    try:
        while True:
            # Send periodic updates about order status
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_status":
                # Get current order status from Redis
                from ..utils.redis_client import RedisService
                status = RedisService.get_order_status(order_id)
                await websocket.send_text(json.dumps({
                    "type": "order_status",
                    "order_id": order_id,
                    "status": status
                }))
                
    except WebSocketDisconnect:
        pass
```

### Phase 9: Main Application Setup (Day 9)

#### 9.1 Create `app/main.py`
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import user_models, order_models, discount_models
from .api import auth_routes, client_routes, driver_routes, admin_routes, websocket_routes
import uvicorn

# Create database tables
user_models.Base.metadata.create_all(bind=engine)
order_models.Base.metadata.create_all(bind=engine)
discount_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Supper Delivery API",
    description="Multi-service delivery platform for food, parcels, medical items, and rides",
    version="1.0.0"
)

# CORS middleware for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(client_routes.router)
app.include_router(driver_routes.router)
app.include_router(admin_routes.router)
app.include_router(websocket_routes.router)

@app.get("/")
def read_root():
    return {"message": "Supper Delivery API v1.0.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Phase 10: Database Migration (Day 9-10)

#### 10.1 Initialize Alembic
```bash
# Initialize Alembic for database migrations
alembic init alembic
```

#### 10.2 Configure `alembic.ini`
```ini
# In alembic.ini, update the sqlalchemy.url
sqlalchemy.url = postgresql://postgres:your_password@localhost/supper_delivery
```

#### 10.3 Update `alembic/env.py`
```python
from app.database import Base
from app.models import user_models, order_models, discount_models

target_metadata = Base.metadata
```

#### 10.4 Create Initial Migration
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Phase 11: Testing Setup (Day 10)

#### 11.1 Create `tests/test_auth.py`
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Supper Delivery API" in response.json()["message"]

# Add more tests for authentication, orders, etc.
```

#### 11.2 Create Test Configuration
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
```

### Phase 12: Docker Setup (Day 10)

#### 12.1 Create `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 12.2 Create `docker-compose.yml`
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/supper_delivery
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: supper_delivery
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Phase 13: API Testing & Validation (Day 11-12)

#### 13.1 Create Sample Data Script
```python
# scripts/create_sample_data.py
from app.database import SessionLocal
from app.models.user_models import User, Client, Driver
from app.models.order_models import Order, OrderType, OrderStatus
from app.models.discount_models import PartnerDiscount

def create_sample_data():
    db = SessionLocal()
    
    # Create sample users
    user1 = User(id="firebase_uid_1", email="client@example.com", full_name="John Client")
    user2 = User(id="firebase_uid_2", email="driver@example.com", full_name="Jane Driver")
    
    db.add_all([user1, user2])
    db.commit()
    
    # Create client and driver profiles
    client = Client(client_id="firebase_uid_1", home_address="123 Main St")
    driver = Driver(driver_id="firebase_uid_2", approved=True, vehicle_type="car")
    
    db.add_all([client, driver])
    db.commit()
    
    # Create sample discount
    discount = PartnerDiscount(name="Hospital ABC", discount_percent=20)
    db.add(discount)
    db.commit()
    
    print("Sample data created successfully!")
    db.close()

if __name__ == "__main__":
    create_sample_data()
```

#### 13.2 API Test Examples
```bash
# Test user registration
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid": "test_uid_123"}'

# Test order creation (with Firebase token)
curl -X POST "http://localhost:8000/client/orders" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "food_delivery",
    "pickup_address": "Restaurant A",
    "dropoff_address": "123 Home Street",
    "special_instructions": "Call when arrived"
  }'

# Test driver getting available orders
curl -X GET "http://localhost:8000/driver/available-orders" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

## Development Timeline

### Week 1: Foundation (Days 1-3)
- ✅ Environment setup
- ✅ Database models
- ✅ Basic authentication

### Week 2: Core Features (Days 4-7)
- ✅ Service layer
- ✅ API endpoints
- ✅ Order management

### Week 3: Real-time & Testing (Days 8-10)
- ✅ WebSocket implementation
- ✅ Testing setup
- ✅ Docker configuration

### Week 4: Deployment & Polish (Days 11-12)
- ✅ API validation
- ✅ Documentation
- ✅ Production ready

## Key Naming Conventions

### Classes
- **Models**: `User`, `Client`, `Driver`, `Order`, `PartnerDiscount`
- **Services**: `UserService`, `OrderService`, `WebSocketService`
- **Schemas**: `UserCreate`, `OrderResponse`, `DriverLocationUpdate`

### Functions
- **Service methods**: `create_user_from_firebase()`, `accept_order()`, `update_order_status()`
- **API endpoints**: `create_order()`, `get_available_orders()`, `approve_driver()`
- **Database methods**: `get_pending_orders()`, `get_client_orders()`

### Variables
- **IDs**: `user_id`, `client_id`, `driver_id`, `order_id`
- **Models**: `current_user`, `current_client`, `current_driver`
- **Data**: `order_data`, `client_data`, `location_data`

### Database Tables
- **users** (Firebase UID as primary key)
- **clients** (references users.id)
- **drivers** (references users.id)
- **orders** (unified for all delivery types)
- **partner_discounts** (admin managed)

## File Dependencies Map

```
main.py
├── database.py
├── config.py
├── models/ (all models)
├── api/ (all routes)
│   ├── auth_routes.py → user_service.py → user_models.py
│   ├── client_routes.py → order_service.py → order_models.py
│   ├── driver_routes.py → order_service.py → redis_client.py
│   └── admin_routes.py → user_service.py
└── services/
    ├── websocket_service.py → redis_client.py
    └── *_service.py → models/ + schemas/
```

## Running the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production with Docker
docker-compose up --build

# Database migrations
alembic upgrade head

# Run tests
pytest tests/
```

This guide provides a complete roadmap for building your Supper Delivery System MVP. Each phase builds upon the previous one, ensuring a logical development flow. The naming conventions are consistent throughout, making the codebase easy to maintain and extend.