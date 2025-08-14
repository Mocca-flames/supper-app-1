# Payment API Endpoints Design

## Payment API Routes

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment_schemas import PaymentCreate, PaymentResponse, PaymentUpdate, RefundCreate, RefundResponse
from ..auth.middleware import get_current_user
from ..schemas.user_schemas import UserResponse

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/create", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new payment record.
    Accessible by clients for their orders and admins for any order.
    """
    try:
        # For client payments, ensure the user is the client
        if payment_data.payment_type == PaymentType.CLIENT_PAYMENT:
            order = db.query(Order).filter(Order.id == payment_data.order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if order.client_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="Not authorized to create payment for this order")

        # For driver payments, ensure the user is the driver or admin
        elif payment_data.payment_type == PaymentType.DRIVER_PAYMENT:
            order = db.query(Order).filter(Order.id == payment_data.order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if order.driver_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="Not authorized to create payment for this order")

        payment = PaymentService.create_payment(db, payment_data, order)
        return payment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating payment")

@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: str,
    update_data: PaymentUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update payment status.
    Accessible by admins or the user who created the payment.
    """
    try:
        payment = PaymentService.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Check authorization
        if payment.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to update this payment")

        updated_payment = PaymentService.update_payment_status(db, payment_id, update_data)
        return updated_payment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating payment status")

@router.post("/refund", response_model=RefundResponse)
def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a refund record.
    Accessible by admins only.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to create refunds")

    try:
        refund = PaymentService.create_refund(db, refund_data)
        return refund

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating refund")

@router.get("/order/{order_id}", response_model=List[PaymentResponse])
def get_order_payments(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all payments for an order.
    Accessible by clients for their orders, drivers for their orders, and admins.
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check authorization
        if (order.client_id != current_user.id and
            order.driver_id != current_user.id and
            not current_user.is_admin):
            raise HTTPException(status_code=403, detail="Not authorized to view payments for this order")

        payments = PaymentService.get_payments_by_order(db, order_id)
        return payments

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving payments")

@router.get("/user/{user_id}", response_model=List[PaymentResponse])
def get_user_payments(
    user_id: str,
    payment_type: Optional[PaymentType] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all payments for a user.
    Accessible by the user themselves or admins.
    """
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view payments for this user")

    try:
        payments = PaymentService.get_payments_by_user(db, user_id, payment_type)
        return payments

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving payments")

@router.get("/refunds/order/{order_id}", response_model=List[RefundResponse])
def get_order_refunds(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all refunds for an order.
    Accessible by clients for their orders, drivers for their orders, and admins.
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check authorization
        if (order.client_id != current_user.id and
            order.driver_id != current_user.id and
            not current_user.is_admin):
            raise HTTPException(status_code=403, detail="Not authorized to view refunds for this order")

        refunds = PaymentService.get_refunds_by_order(db, order_id)
        return refunds

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving refunds")
```

## Key Features

1. **Secure Access Control**: Proper authorization for all endpoints
2. **Comprehensive Payment Management**: Create, update, and retrieve payments
3. **Refund Support**: Full refund lifecycle management
4. **Order Integration**: All endpoints work with order context
5. **User Context**: Endpoints consider both client and driver perspectives
6. **Admin Capabilities**: Special admin-only endpoints for sensitive operations
7. **Flexible Queries**: Multiple ways to retrieve payment information