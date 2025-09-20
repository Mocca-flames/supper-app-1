# Corporate System Integration Plan for Existing FastAPI

## Overview

Your current API already has excellent foundations. We'll add corporate features that work with your existing structure for Events, Working Class, and School Transportation.

## Phase 1: Corporate Entities (New FastAPI Routes)

### 1.1 Corporate Account Management

```python
# New routes to add:
POST   /api/corporate/register          # Register corporate account
GET    /api/corporate/profile           # Get corporate profile
PUT    /api/corporate/profile           # Update corporate profile
GET    /api/corporate/accounts          # Admin: List all corporate accounts
```

### 1.2 Database Models to Add

```python
# Add to your existing models
class CorporateAccount(Base):
    __tablename__ = "corporate_accounts"

    id: str = Column(String, primary_key=True)
    company_name: str = Column(String, nullable=False)
    contact_email: str = Column(String, nullable=False)
    contact_phone: str = Column(String, nullable=True)
    account_type: str = Column(Enum("event", "employer", "school"), nullable=False)
    billing_address: str = Column(String, nullable=True)
    credit_limit: decimal = Column(Numeric(10,2), default=0)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscriptions = relationship("CorporateSubscription", back_populates="corporate_account")
    bulk_orders = relationship("BulkOrder", back_populates="corporate_account")
```

## Phase 2: Extend Existing Order System

### 2.1 Modify Your Existing OrderCreate Schema

```python
# Extend your existing OrderCreate to support corporate features
class OrderCreate(BaseModel):
    # Your existing fields...
    order_type: OrderType
    pickup_address: str
    # ... existing fields ...

    # ADD these new optional fields:
    corporate_account_id: Optional[str] = None
    is_scheduled: bool = False
    scheduled_for: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "daily", "weekly", etc.
    group_size: Optional[int] = None
    cost_center: Optional[str] = None
```

### 2.2 New Corporate-Specific Routes

```python
# ADD these routes to your existing structure:
POST   /api/corporate/orders/bulk       # Create multiple orders at once
POST   /api/corporate/orders/recurring  # Set up recurring orders
GET    /api/corporate/orders/scheduled  # Get scheduled orders
PUT    /api/corporate/orders/{order_id}/reschedule
```

## Phase 3: Subscription & Billing System

### 3.1 Corporate Subscriptions

```python
# New routes:
POST   /api/corporate/subscriptions     # Create subscription plan
GET    /api/corporate/subscriptions     # Get active subscriptions
PUT    /api/corporate/subscriptions/{sub_id}
DELETE /api/corporate/subscriptions/{sub_id}
```

### 3.2 Extend Your Payment System

```python
# ADD to your existing PaymentCreate:
class PaymentCreate(BaseModel):
    # Your existing fields...

    # ADD these:
    corporate_account_id: Optional[str] = None
    is_corporate_billing: bool = False
    billing_period: Optional[str] = None
```

## Phase 4: Specialized Service Types

### 4.1 Extend Your OrderType Enum

```python
# Modify your existing OrderType enum:
class OrderType(str, Enum):
    # Your existing types...
    ride = "ride"
    food_delivery = "food_delivery"
    parcel_delivery = "parcel_delivery"
    medical_product = "medical_product"
    patient_transport = "patient_transport"

    # ADD these new types:
    event_shuttle = "event_shuttle"
    employee_transport = "employee_transport"
    school_transport = "school_transport"
    group_ride = "group_ride"
```

## Phase 5: Integration Points with Your Current System

### 5.1 Enhance Your Admin Routes

```python
# ADD to your existing admin endpoints:
GET    /api/admin/corporate/accounts
GET    /api/admin/corporate/billing-summary
POST   /api/admin/corporate/{corp_id}/credit-adjustment
GET    /api/admin/corporate/orders/analytics
```

### 5.2 Driver Assignment Logic

```python
# Enhance your existing driver assignment in:
# /api/driver/available-orders
# Add filters for:
# - Corporate orders (might pay more)
# - Scheduled orders
# - Group rides
# - Event shuttles
```

## Implementation Strategy

### Step 1: Database Migration

```python
# Add new tables to your existing database:
# - corporate_accounts
# - corporate_subscriptions
# - bulk_orders
# - scheduled_orders
```

### Step 2: Modify Existing Endpoints

- Extend your `OrderCreate` schema
- Update order creation logic to handle corporate features
- Enhance your admin dashboard with corporate data

### Step 3: New Corporate Endpoints

- Add corporate registration/management
- Add bulk order creation
- Add subscription management

### Step 4: Enhanced Driver Experience

- Show corporate orders in driver app
- Add filters for high-value corporate rides
- Implement group ride coordination

## Quick Implementation Example

```python
# New corporate router to add to your FastAPI app:
from fastapi import APIRouter, Depends
from your_existing_auth import get_current_user

corporate_router = APIRouter(prefix="/api/corporate", tags=["Corporate"])

@corporate_router.post("/register")
async def register_corporate_account(
    account_data: CorporateAccountCreate,
    current_user = Depends(get_current_user)
):
    # Create corporate account
    # Link to current user
    pass

@corporate_router.post("/orders/bulk")
async def create_bulk_orders(
    bulk_data: BulkOrderCreate,
    current_user = Depends(get_current_user)
):
    # Create multiple orders using your existing order creation logic
    # But with corporate account linkage
    pass

# Add to your main app:
app.include_router(corporate_router)
```

## Benefits of This Approach

1. **Minimal Disruption**: Works with your existing user/driver/order system
2. **Incremental**: Can implement one feature at a time
3. **Scalable**: Builds on your solid foundation
4. **Reusable**: Uses your existing payment and order infrastructure

## Next Steps

1. Database migration,
