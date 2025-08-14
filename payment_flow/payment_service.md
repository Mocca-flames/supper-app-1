# Payment Service Layer Design

## PaymentService Class

```python
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import logging

from ..models.payment_models import Payment, Refund, PaymentStatus, PaymentType
from ..models.order_models import Order
from ..schemas.payment_schemas import PaymentCreate, PaymentUpdate, RefundCreate

# Configure logger
logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    def create_payment(
        db: Session,
        payment_data: PaymentCreate,
        order: Optional[Order] = None
    ) -> Payment:
        """Create a new payment record"""
        logger.info(f"💰 Creating payment: {payment_data.payment_type.value} - R{payment_data.amount}")

        try:
            # Validate order exists and get current order if not provided
            if not order:
                order = db.query(Order).filter(Order.id == payment_data.order_id).first()
                if not order:
                    logger.error(f"❌ Order not found: {payment_data.order_id}")
                    raise ValueError("Order not found")

            # Create payment record
            payment = Payment(
                order_id=payment_data.order_id,
                user_id=payment_data.user_id,
                payment_type=payment_data.payment_type,
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=payment_data.payment_method,
                status=PaymentStatus.PENDING,
                transaction_id=payment_data.transaction_id,
                transaction_details=payment_data.transaction_details
            )

            db.add(payment)

            # Update order payment status and totals
            if payment_data.payment_type == PaymentType.CLIENT_PAYMENT:
                order.total_paid += payment_data.amount
                if order.total_paid >= order.price:
                    order.payment_status = PaymentStatus.COMPLETED
                else:
                    order.payment_status = PaymentStatus.PARTIAL
            elif payment_data.payment_type == PaymentType.DRIVER_PAYMENT:
                # For driver payments, we might want to track separately
                # This could be implemented differently based on requirements
                pass

            db.commit()
            db.refresh(payment)
            db.refresh(order)

            logger.info(f"✅ Payment created: {payment.id}")
            return payment

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error creating payment: {str(e)}")
            db.rollback()
            raise ValueError(f"Error creating payment: {str(e)}") from e

    @staticmethod
    def update_payment_status(
        db: Session,
        payment_id: str,
        update_data: PaymentUpdate
    ) -> Payment:
        """Update payment status and related order status"""
        logger.info(f"🔄 Updating payment status: {payment_id} → {update_data.status.value}")

        try:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                logger.error(f"❌ Payment not found: {payment_id}")
                raise ValueError("Payment not found")

            order = db.query(Order).filter(Order.id == payment.order_id).first()
            if not order:
                logger.error(f"❌ Order not found for payment: {payment.order_id}")
                raise ValueError("Order not found")

            # Update payment status
            old_status = payment.status
            payment.status = update_data.status
            payment.transaction_id = update_data.transaction_id or payment.transaction_id
            payment.transaction_details = update_data.transaction_details or payment.transaction_details
            payment.updated_at = datetime.utcnow()

            # Update order status if needed
            if payment.payment_type == PaymentType.CLIENT_PAYMENT:
                if update_data.status == PaymentStatus.COMPLETED:
                    # Check if all payments are complete
                    total_paid = db.query(func.sum(Payment.amount)).filter(
                        Payment.order_id == order.id,
                        Payment.payment_type == PaymentType.CLIENT_PAYMENT,
                        Payment.status == PaymentStatus.COMPLETED
                    ).scalar() or Decimal("0")

                    if total_paid >= order.price:
                        order.payment_status = PaymentStatus.COMPLETED
                    else:
                        order.payment_status = PaymentStatus.PARTIAL
                elif update_data.status in [PaymentStatus.FAILED, PaymentStatus.REFUNDED]:
                    # Recalculate total paid
                    total_paid = db.query(func.sum(Payment.amount)).filter(
                        Payment.order_id == order.id,
                        Payment.payment_type == PaymentType.CLIENT_PAYMENT,
                        Payment.status == PaymentStatus.COMPLETED
                    ).scalar() or Decimal("0")

                    order.total_paid = total_paid
                    if total_paid >= order.price:
                        order.payment_status = PaymentStatus.COMPLETED
                    elif total_paid > 0:
                        order.payment_status = PaymentStatus.PARTIAL
                    else:
                        order.payment_status = PaymentStatus.PENDING

            db.commit()
            db.refresh(payment)
            db.refresh(order)

            logger.info(f"✅ Payment status updated: {old_status.value} → {payment.status.value}")
            return payment

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error updating payment: {str(e)}")
            db.rollback()
            raise ValueError(f"Error updating payment: {str(e)}") from e

    @staticmethod
    def create_refund(
        db: Session,
        refund_data: RefundCreate
    ) -> Refund:
        """Create a refund record"""
        logger.info(f"🔄 Creating refund: R{refund_data.amount} for payment {refund_data.payment_id}")

        try:
            # Validate payment exists
            payment = db.query(Payment).filter(Payment.id == refund_data.payment_id).first()
            if not payment:
                logger.error(f"❌ Payment not found: {refund_data.payment_id}")
                raise ValueError("Payment not found")

            order = db.query(Order).filter(Order.id == refund_data.order_id).first()
            if not order:
                logger.error(f"❌ Order not found: {refund_data.order_id}")
                raise ValueError("Order not found")

            # Create refund record
            refund = Refund(
                payment_id=refund_data.payment_id,
                order_id=refund_data.order_id,
                amount=refund_data.amount,
                reason=refund_data.reason,
                status=PaymentStatus.PENDING
            )

            db.add(refund)

            # Update payment and order status
            if payment.status == PaymentStatus.COMPLETED:
                payment.status = PaymentStatus.PARTIAL
            elif payment.status == PaymentStatus.PARTIAL:
                # Check if full refund
                total_refunded = db.query(func.sum(Refund.amount)).filter(
                    Refund.payment_id == payment.id,
                    Refund.status == PaymentStatus.COMPLETED
                ).scalar() or Decimal("0")

                if total_refunded + refund_data.amount >= payment.amount:
                    payment.status = PaymentStatus.REFUNDED

            # Update order totals
            order.total_refunded += refund_data.amount
            total_paid = order.total_paid - refund_data.amount
            if total_paid >= order.price:
                order.payment_status = PaymentStatus.COMPLETED
            elif total_paid > 0:
                order.payment_status = PaymentStatus.PARTIAL
            else:
                order.payment_status = PaymentStatus.PENDING

            db.commit()
            db.refresh(refund)
            db.refresh(payment)
            db.refresh(order)

            logger.info(f"✅ Refund created: {refund.id}")
            return refund

        except SQLAlchemyError as e:
            logger.error(f"❌ Database error creating refund: {str(e)}")
            db.rollback()
            raise ValueError(f"Error creating refund: {str(e)}") from e

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        logger.info(f"🔍 Getting payment: {payment_id}")
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_payments_by_order(db: Session, order_id: str) -> List[Payment]:
        """Get all payments for an order"""
        logger.info(f"🔍 Getting payments for order: {order_id}")
        return db.query(Payment).filter(Payment.order_id == order_id).all()

    @staticmethod
    def get_payments_by_user(db: Session, user_id: str, payment_type: Optional[PaymentType] = None) -> List[Payment]:
        """Get all payments for a user"""
        logger.info(f"🔍 Getting payments for user: {user_id}")

        query = db.query(Payment).filter(Payment.user_id == user_id)
        if payment_type:
            query = query.filter(Payment.payment_type == payment_type)

        return query.all()

    @staticmethod
    def get_refunds_by_order(db: Session, order_id: str) -> List[Refund]:
        """Get all refunds for an order"""
        logger.info(f"🔍 Getting refunds for order: {order_id}")
        return db.query(Refund).filter(Refund.order_id == order_id).all()
```

## Key Features

1. **Comprehensive Payment Management**: Create, update, and retrieve payments
2. **Order Integration**: Automatically updates order payment status and totals
3. **Refund Support**: Full refund lifecycle management
4. **Status Workflow**: Proper status transitions for payments and orders
5. **Transaction Safety**: Database transactions with rollback on errors
6. **Detailed Logging**: Comprehensive logging for all operations
7. **Flexible Queries**: Multiple ways to retrieve payment information