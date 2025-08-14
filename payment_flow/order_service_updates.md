# Order Service Updates for Payment Integration

## Updated OrderService Class

```python
from sqlalchemy import func
from ..models.payment_models import Payment, PaymentType, PaymentStatus

class OrderService:
    # ... existing methods ...

    @staticmethod
    def create_order(db: Session, order_data: OrderCreate, admin_custom_price: Optional[Decimal] = None) -> Order:
        """Create a new order with payment initialization"""
        # ... existing order creation logic ...

        # Initialize payment status
        order.payment_status = PaymentStatus.PENDING
        order.total_paid = Decimal("0.00")
        order.total_refunded = Decimal("0.00")

        # ... rest of order creation logic ...

        return order

    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        """Update order status with payment status validation"""
        # ... existing status update logic ...

        # Additional payment status validation
        order = db.query(Order).filter(Order.id == order_id).first()

        # If order is being completed, ensure payment is complete
        if new_status == OrderStatus.COMPLETED:
            total_paid = db.query(func.sum(Payment.amount)).filter(
                Payment.order_id == order_id,
                Payment.payment_type == PaymentType.CLIENT_PAYMENT,
                Payment.status == PaymentStatus.COMPLETED
            ).scalar() or Decimal("0")

            if total_paid < order.price:
                raise ValueError("Cannot complete order until full payment is received")

        # ... rest of status update logic ...

        return order

    @staticmethod
    def get_order_payment_status(db: Session, order_id: str) -> dict:
        """Get detailed payment status for an order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")

        # Get all payments for the order
        payments = db.query(Payment).filter(Payment.order_id == order_id).all()

        # Calculate totals
        total_paid = db.query(func.sum(Payment.amount)).filter(
            Payment.order_id == order_id,
            Payment.payment_type == PaymentType.CLIENT_PAYMENT,
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or Decimal("0")

        total_refunded = db.query(func.sum(Payment.amount)).filter(
            Payment.order_id == order_id,
            Payment.payment_type == PaymentType.CLIENT_PAYMENT,
            Payment.status == PaymentStatus.REFUNDED
        ).scalar() or Decimal("0")

        return {
            "order_id": order_id,
            "payment_status": order.payment_status.value,
            "total_paid": float(total_paid),
            "total_refunded": float(total_refunded),
            "outstanding_balance": float(order.price - total_paid),
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "status": p.status.value,
                    "method": p.payment_method.value,
                    "created_at": p.created_at.isoformat()
                } for p in payments
            ]
        }

    @staticmethod
    def process_order_payment(
        db: Session,
        order_id: str,
        payment_data: PaymentCreate
    ) -> Order:
        """Process a payment for an order and update order status"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")

        # Create payment
        payment = PaymentService.create_payment(db, payment_data, order)

        # Update order payment status
        total_paid = db.query(func.sum(Payment.amount)).filter(
            Payment.order_id == order_id,
            Payment.payment_type == PaymentType.CLIENT_PAYMENT,
            Payment.status == PaymentStatus.COMPLETED
        ).scalar() or Decimal("0")

        order.total_paid = total_paid

        if total_paid >= order.price:
            order.payment_status = PaymentStatus.COMPLETED
        elif total_paid > 0:
            order.payment_status = PaymentStatus.PARTIAL

        db.commit()
        db.refresh(order)

        return order
```

## Key Updates

1. **Payment Initialization**: Orders now initialize with payment status fields
2. **Payment Validation**: Order completion requires full payment
3. **Payment Status Methods**: New methods to get detailed payment status
4. **Payment Processing**: Integrated payment processing in order workflow
5. **Status Synchronization**: Order status and payment status are synchronized