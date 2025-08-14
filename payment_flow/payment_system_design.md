# Payment Management System Design Documentation

## Overview

This document provides a comprehensive design for the Payment Management System that integrates with the existing order system. The system is designed to be flexible, supporting multiple payment methods and integrating with the order lifecycle.

## Key Features

1. **Flexible Payment Methods**: Supports credit card, mobile money, cash, and other methods
2. **Dual Payment Tracking**: Tracks both client payments (to platform) and driver payments (from platform)
3. **Payment Status Integration**: Integrates with order status workflow
4. **Partial Payments**: Supports partial payments and refunds
5. **Transaction Safety**: Proper database transactions with rollback on errors
6. **Comprehensive API**: Full CRUD operations for payments and refunds
7. **Secure Access Control**: Proper authorization for all operations

## Components

### Database Models

#### Payment Model

```python
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    user_id = Column(String, nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="ZAR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)
    transaction_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="payments")
```

#### Refund Model

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

#### Order Model Updates

```python
class Order(Base):
    # ... existing fields ...

    # Payment integration fields
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_paid = Column(Numeric(10, 2), default=0.00)
    total_refunded = Column(Numeric(10, 2), default=0.00)

    # Relationships
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")
```

### Schemas

#### Payment Schemas

```python
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
```

### Service Layer

#### PaymentService

```python
class PaymentService:
    @staticmethod
    def create_payment(db: Session, payment_data: PaymentCreate, order: Optional[Order] = None) -> Payment:
        """Create a new payment record with order integration"""
        # ... implementation ...

    @staticmethod
    def update_payment_status(db: Session, payment_id: str, update_data: PaymentUpdate) -> Payment:
        """Update payment status and related order status"""
        # ... implementation ...

    @staticmethod
    def create_refund(db: Session, refund_data: RefundCreate) -> Refund:
        """Create a refund record with order integration"""
        # ... implementation ...
```

### API Endpoints

#### Payment Routes

```python
@router.post("/create", response_model=PaymentResponse)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    """Create a new payment with proper authorization"""
    # ... implementation ...

@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(payment_id: str, update_data: PaymentUpdate, db: Session = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    """Update payment status with authorization checks"""
    # ... implementation ...
```

## Workflow

### Payment Processing Flow

1. **Order Creation**: Order is created with PENDING payment status
2. **Payment Initiation**: Client initiates payment through API
3. **Payment Processing**: PaymentService processes payment and updates order
4. **Status Updates**: Payment status changes trigger order status updates
5. **Completion**: When full payment is received, order can be completed
6. **Refunds**: Payments can be refunded if needed

### Refund Processing Flow

1. **Refund Request**: Admin initiates refund through API
2. **Refund Processing**: PaymentService processes refund and updates payment/order
3. **Status Updates**: Refund status changes update payment and order status
4. **Completion**: Refund is marked as completed when processed

## Database Migration

The system includes a comprehensive Alembic migration that:

1. Creates necessary enum types
2. Creates payments and refunds tables
3. Adds payment fields to orders table
4. Sets up proper foreign key relationships
5. Includes full rollback capability

## Security

1. **Authorization**: All endpoints check user permissions
2. **Data Validation**: Pydantic schemas validate all input
3. **Transaction Safety**: Database operations use transactions with rollback
4. **Audit Trail**: All changes are logged with timestamps

## Extensibility

1. **Payment Methods**: Easy to add new payment methods
2. **Status Workflows**: Status transitions can be customized
3. **Integration**: Can integrate with external payment gateways
4. **Reporting**: Comprehensive data for analytics and reporting