from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import logging
import json

from ..models.payment_models import Payment, Refund, PaymentStatus, PaymentType, PaymentGateway
from ..models.order_models import Order
from ..schemas.payment_schemas import PaymentCreate, PaymentUpdate, RefundCreate
from ..utils.redis_client import RedisService
import hashlib
import requests
from ..config import settings
from ..models.user_models import User # Added for fetching user details

# Configure logger
logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    def create_payment(
        db: Session,
        payment_data: PaymentCreate,
        order: Optional[Order] = None
    ) -> Payment:
        """Create a new payment record and process through mock gateway"""
        logger.info(f"💰 Creating payment: {payment_data.payment_type.value} - R{payment_data.amount}")

        try:
            # Validate order exists and get current order if not provided
            if not order:
                order = db.query(Order).filter(Order.id == payment_data.order_id).first()
                if not order:
                    logger.error(f"❌ Order not found: {payment_data.order_id}")
                    raise ValueError("Order not found")

            # Ensure transaction_details is properly JSON encoded
            transaction_details_json = None
            if payment_data.transaction_details:
                if isinstance(payment_data.transaction_details, str):
                    # Already JSON string, validate it's valid JSON
                    try:
                        json.loads(payment_data.transaction_details)
                        transaction_details_json = payment_data.transaction_details
                    except json.JSONDecodeError:
                        logger.error(f"❌ Invalid JSON in transaction_details: {payment_data.transaction_details}")
                        raise ValueError("Invalid JSON in transaction_details")
                elif isinstance(payment_data.transaction_details, dict):
                    # Convert dict to JSON string
                    transaction_details_json = json.dumps(payment_data.transaction_details)
                else:
                    # Convert other types to JSON string
                    transaction_details_json = json.dumps(payment_data.transaction_details)

            # Create payment record with PENDING status
            payment = Payment(
                order_id=payment_data.order_id,
                user_id=payment_data.user_id,
                payment_type=payment_data.payment_type,
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=payment_data.payment_method,
                gateway=payment_data.gateway,
                status=PaymentStatus.PENDING,
                transaction_id=payment_data.transaction_id,
                transaction_details=transaction_details_json
            )

            db.add(payment)
            db.commit()
            db.refresh(payment)

            # Fetch user details for payment
            user = db.query(User).filter(User.id == payment_data.user_id).first()
            if not user:
                logger.error(f"❌ User not found for payment: {payment_data.user_id}")
                raise ValueError("User not found for payment")

            # Prepare PayFast payment data
            payfast_environment = settings.PAYFAST_ENVIRONMENT
            if payfast_environment == "production":
                base_url = settings.PAYFAST_PRODUCTION_URL
            else:
                base_url = settings.PAYFAST_SANDBOX_URL

            merchant_id = settings.PAYFAST_MERCHANT_ID
            merchant_key = settings.PAYFAST_MERCHANT_KEY
            passphrase = getattr(settings, "PAYFAST_PASSPHRASE", "")

            # Build payment data dictionary
            payfast_data = {
                "merchant_id": merchant_id,
                "merchant_key": merchant_key,
                "return_url": settings.PAYFAST_RETURN_URL,
                "cancel_url": settings.PAYFAST_CANCEL_URL,
                "name_first": user.first_name,
                "name_last": user.last_name,
                "email_address": user.email,
                "m_payment_id": str(payment.id),
                "amount": f"{payment.amount:.2f}",
                "item_name": "Order Payment",
                "item_description": f"Payment for order {payment.order_id}",
            }

            # Generate signature
            def generate_signature(data, passphrase=""):
                query_string = ""
                for key in sorted(data.keys()):
                    value = data[key]
                    if value is not None and value != "": # Ensure None values are not included
                        query_string += f"{key}={requests.utils.quote(str(value).strip())}&"
                query_string = query_string[:-1]
                if passphrase:
                    query_string += f"&passphrase={requests.utils.quote(passphrase.strip())}"
                return hashlib.md5(query_string.encode("utf-8")).hexdigest()

            signature = generate_signature(payfast_data, passphrase)
            payfast_data["signature"] = signature

            # For now, mark payment as PENDING and store transaction details
            payment.status = PaymentStatus.PENDING
            payment.transaction_id = None # This will be updated by PayFast callback
            payment.transaction_details = json.dumps(payfast_data)

            db.commit()
            db.refresh(payment)
            db.refresh(order)

            logger.info(f"✅ Payment created: {payment.id} with status {payment.status.value}")
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
            
            # Handle transaction_details JSON conversion
            if update_data.transaction_details:
                if isinstance(update_data.transaction_details, str):
                    payment.transaction_details = update_data.transaction_details
                else:
                    payment.transaction_details = json.dumps(update_data.transaction_details)
            
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
        """Create a refund record and process through mock gateway"""
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

            # TODO: Implement actual PayFast refund API call here
            # For now, simulate a pending refund
            refund_status = PaymentStatus.PENDING

            refund = Refund(
                payment_id=refund_data.payment_id,
                order_id=refund_data.order_id,
                amount=refund_data.amount,
                reason=refund_data.reason,
                status=refund_status
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

            logger.info(f"✅ Refund created: {refund.id} with status {refund.status.value}")
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