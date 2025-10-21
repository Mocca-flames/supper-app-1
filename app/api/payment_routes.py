from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import json # Added for json.loads
import os # Added for os.getenv
import httpx # Added for HTTP requests to PayFast API
import hashlib # Added for MD5 signature generation
import urllib.parse # Added for URL encoding
from datetime import datetime # Added for timestamp generation
import logging # Added for logging
import hmac # Added for HMAC signature verification

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment_schemas import PaymentCreate, PaymentResponse, PaymentUpdate, RefundCreate, RefundResponse
from ..auth.middleware import get_current_user
from ..schemas.user_schemas import UserResponse
from ..models.payment_models import PaymentStatus, PaymentType, PaymentGateway
from ..models.order_models import Order
from ..config import settings # Added for settings

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)

@router.post("/paystack/initialize")
def initialize_paystack_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Initialize a Paystack payment transaction.
    Creates payment record and calls Paystack API to get access_code for frontend.
    """
    try:
        # Override gateway to Paystack
        payment_data.gateway = PaymentGateway.PAYSTACK

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

        # Create payment record
        payment = PaymentService.create_payment(db, payment_data, order)

        # Get user details for Paystack
        order = db.query(Order).filter(Order.id == payment_data.order_id).first()
        if payment_data.payment_type == PaymentType.CLIENT_PAYMENT:
            user_id = order.client_id
        else:
            user_id = order.driver_id

        from ..models.user_models import User
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prepare Paystack initialization data
        logger.info(f"Paystack init: payment.amount type={type(payment.amount)}, value={payment.amount}")
        
        try:
            amount_kobo = int(payment.amount * 100)  # Convert to kobo (multiply by 100)
        except Exception as e:
            logger.error(f"❌ Error converting amount to kobo: {e}")
            raise HTTPException(status_code=500, detail=f"Internal error: Failed to convert amount for Paystack. {e}")

        paystack_data = {
            "email": user.email,
            "amount": amount_kobo,
            "currency": payment.currency,
            "reference": payment.id,  # Use payment ID as reference
            "callback_url": getattr(settings, "PAYSTACK_CALLBACK_URL", " http://56.228.32.209:8000/api/payments/callback")
        }

        # Call Paystack API
        try:
            paystack_secret_key = settings.PAYSTACK_SECRET_KEY
            headers = {
                "Authorization": f"Bearer {paystack_secret_key}",
                "Content-Type": "application/json"
            }

            with httpx.Client() as client:
                response = client.post(
                    "https://api.paystack.co/transaction/initialize",
                    json=paystack_data,
                    headers=headers,
                    timeout=30.0
                )
        except AttributeError as e:
            logger.error(f"❌ Configuration error: {e}")
            raise HTTPException(status_code=500, detail=f"Configuration error: Paystack secret key missing. {e}")
        except httpx.RequestError as e:
            logger.error(f"❌ HTTP request error to Paystack: {e}")
            raise HTTPException(status_code=502, detail=f"Paystack API request failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error during Paystack API call setup: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error during Paystack API call setup: {e}")


        if response.status_code != 200:
            logger.error(f"❌ Paystack API returned non-200 status: {response.status_code}, body: {response.text}")
            raise HTTPException(status_code=502, detail=f"Paystack API error: {response.text}")

        try:
            paystack_response = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to decode Paystack response JSON: {e}, raw text: {response.text}")
            raise HTTPException(status_code=502, detail=f"Paystack API returned invalid JSON: {e}")

        if not paystack_response.get("status"):
            logger.error(f"❌ Paystack initialization failed: {paystack_response}")
            raise HTTPException(status_code=502, detail=f"Paystack initialization failed: {paystack_response}")

        try:
            access_code = paystack_response["data"]["access_code"]
        except KeyError as e:
            logger.error(f"❌ Missing key in Paystack response: {e}, response: {paystack_response}")
            raise HTTPException(status_code=502, detail=f"Paystack response missing required data: {e}")


        # Update payment with Paystack reference
        payment.transaction_id = paystack_response["data"]["reference"]
        payment.transaction_details = json.dumps(paystack_response["data"])
        db.commit()

        return {
            "payment": payment,
            "access_code": access_code,
            "authorization_url": paystack_response["data"]["authorization_url"]
        }

    except ValueError as e:
        logger.error(f"❌ Value error caught: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise specific HTTPExceptions (400, 403, 404, 502)
        raise
    except Exception as e:
        logger.error(f"❌ Unhandled error initializing Paystack payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error initializing Paystack payment")

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

        # Handle different gateways
        if payment.gateway == PaymentGateway.PAYFAST:
            # Return payment with payment gateway redirect URL or instructions
            payfast_environment = os.getenv("PAYFAST_ENVIRONMENT", "sandbox")
            if payfast_environment == "production":
                base_url = os.getenv("PAYFAST_PRODUCTION_URL", "https://www.payfast.co.za")
            else:
                base_url = os.getenv("PAYFAST_SANDBOX_URL", "https://sandbox.payfast.co.za")

            # The payment.transaction_details contains the form data for PayFast
            form_data = json.loads(payment.transaction_details or "{}")

            # Construct the form action URL
            payment_url = f"{base_url}/eng/process"

            # Return payment info along with payment_url and form_data for frontend to submit
            return {
                "payment": payment,
                "payment_url": payment_url,
                "form_data": form_data
            }
        elif payment.gateway == PaymentGateway.PAYSTACK:
            # For Paystack, client should use /paystack/initialize endpoint
            raise HTTPException(status_code=400, detail="Use /payments/paystack/initialize for Paystack payments")
        else:
            # Default response for other gateways
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

@router.get("/query/{pf_payment_id}")
def query_payfast_transaction(
    pf_payment_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Query PayFast for transaction status using pf_payment_id.
    This provides server-side verification of payment status directly from PayFast.
    """
    import base64
    try:
        # Get PayFast configuration from settings
        payfast_environment = os.getenv("PAYFAST_ENVIRONMENT", "sandbox")
        if payfast_environment == "production":
            base_url = os.getenv("PAYFAST_PRODUCTION_URL", "https://www.payfast.co.za")
            merchant_id = os.getenv("PAYFAST_PRODUCTION_MERCHANT_ID")
            merchant_key = os.getenv("PAYFAST_PRODUCTION_MERCHANT_KEY")
            passphrase = os.getenv("PAYFAST_PRODUCTION_PASSPHRASE")
        else:
            base_url = os.getenv("PAYFAST_SANDBOX_URL", "https://sandbox.payfast.co.za")
            merchant_id = os.getenv("PAYFAST_SANDBOX_MERCHANT_ID")
            merchant_key = os.getenv("PAYFAST_SANDBOX_MERCHANT_KEY")
            passphrase = os.getenv("PAYFAST_SANDBOX_PASSPHRASE")

        if not all([merchant_id, merchant_key]):
            raise HTTPException(status_code=500, detail="PayFast credentials not configured")

        # Prepare query data
        timestamp = datetime.utcnow().isoformat()
        query_data = {
            "merchant_id": merchant_id,
            "version": "v1",
            "timestamp": timestamp
        }

        # Generate signature for query request
        signature_string = f"merchant_id={urllib.parse.quote(str(merchant_id))}&version=v1&timestamp={urllib.parse.quote(timestamp)}"
        if passphrase:
            signature_string += f"&passphrase={urllib.parse.quote(passphrase)}"
        signature = hashlib.md5(signature_string.encode()).hexdigest()

        # Prepare query parameters
        query_params = {
            "merchant_id": merchant_id,
            "version": "v1",
            "timestamp": timestamp,
            "signature": signature
        }

        # Make request to PayFast API
        query_url = f"{base_url}/api/v1/transactions/{pf_payment_id}/query"
        auth_string = f"{merchant_id}:{merchant_key}"
        auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"

        with httpx.Client() as client:
            response = client.get(
                query_url,
                params=query_params,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PayFast API error: {response.text}"
            )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PayFast API request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"PayFast API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying PayFast transaction: {str(e)}")

@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Paystack webhook notifications for payment verification.
    Paystack sends this when a transaction is completed.
    """
    try:
        # Get raw request body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8')

        # Verify webhook signature (required for production security)
        signature_header = request.headers.get('x-paystack-signature')
        if not signature_header:
            logger.error("❌ Missing Paystack signature header")
            raise HTTPException(status_code=400, detail="Missing signature header")

        paystack_secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
        expected_signature = hmac.new(
            paystack_secret,
            body,
            hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature_header):
            logger.error("❌ Invalid Paystack webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse the JSON payload
        try:
            request_data = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        event = request_data.get("event")
        data = request_data.get("data", {})

        if event == "charge.success":
            reference = data.get("reference")
            status = data.get("status")
            amount_kobo = data.get("amount")  # in kobo

            if not reference:
                logger.error("❌ Missing reference in charge.success event")
                raise HTTPException(status_code=400, detail="Missing reference in webhook data")

            if status == "success":
                # Find payment by reference
                payment = PaymentService.get_payment_by_id(db, reference)
                if not payment:
                    logger.error(f"❌ Payment not found: {reference}")
                    raise HTTPException(status_code=404, detail="Payment not found")

                if payment.gateway != PaymentGateway.PAYSTACK:
                    logger.error(f"❌ Payment gateway mismatch: expected Paystack, got {payment.gateway}")
                    raise HTTPException(status_code=400, detail="Invalid payment gateway")

                # Verify amount matches expected payment amount
                expected_amount_kobo = int(payment.amount * 100)
                if amount_kobo != expected_amount_kobo:
                    logger.error(f"❌ Amount mismatch for payment {payment.id}: expected {expected_amount_kobo} kobo, got {amount_kobo} kobo")
                    raise HTTPException(status_code=400, detail="Payment amount mismatch")

                # Get the associated order to check remaining balance
                order = db.query(Order).filter(Order.id == payment.order_id).first()
                if not order:
                    logger.error(f"❌ Order not found for payment {payment.id}: {payment.order_id}")
                    raise HTTPException(status_code=404, detail="Associated order not found")

                # Calculate remaining amount to be paid (order price - already paid)
                remaining_amount = order.price - order.total_paid
                payment_amount = payment.amount

                if payment_amount > remaining_amount:
                    logger.error(f"❌ Payment amount exceeds remaining order balance: payment={payment_amount}, remaining={remaining_amount}")
                    # Mark payment as failed and update order status
                    PaymentService.update_payment_status(
                        db,
                        payment.id,
                        PaymentUpdate(status=PaymentStatus.FAILED, transaction_id=reference)
                    )
                    raise HTTPException(status_code=400, detail="Payment amount exceeds order balance")

                # Check for duplicate payment (if transaction_id is already set)
                if payment.transaction_id and payment.transaction_id != reference:
                    logger.warning(f"⚠️ Potential duplicate payment detected for reference {reference}")
                    # Allow the webhook to proceed but log the issue

                # Update payment status to completed
                try:
                    PaymentService.update_payment_status(
                        db,
                        payment.id,
                        PaymentUpdate(status=PaymentStatus.COMPLETED, transaction_id=reference)
                    )
                    logger.info(f"✅ Payment {payment.id} marked as completed via webhook")
                    return {"status": "success"}
                except Exception as update_error:
                    logger.error(f"❌ Failed to update payment status: {str(update_error)}")
                    raise HTTPException(status_code=500, detail="Failed to update payment status")

            else:
                logger.warning(f"⚠️ Received charge.success event with non-success status: {status}")

        elif event == "charge.failed":
            reference = data.get("reference")
            if reference:
                payment = PaymentService.get_payment_by_id(db, reference)
                if payment and payment.gateway == PaymentGateway.PAYSTACK:
                    try:
                        PaymentService.update_payment_status(
                            db,
                            payment.id,
                            PaymentUpdate(status=PaymentStatus.FAILED, transaction_id=reference)
                        )
                        logger.info(f"✅ Payment {payment.id} marked as failed via webhook")
                    except Exception as update_error:
                        logger.error(f"❌ Failed to update failed payment status: {str(update_error)}")

        else:
            logger.info(f"ℹ️ Ignoring unhandled webhook event: {event}")

        return {"status": "ignored"}

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error processing Paystack webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing webhook")

@router.get("/paystack/verify/{reference}")
def verify_paystack_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Manually verify a Paystack payment using the transaction reference.
    """
    try:
        # Find payment by reference
        payment = PaymentService.get_payment_by_id(db, reference)
        if not payment or payment.gateway != PaymentGateway.PAYSTACK:
            raise HTTPException(status_code=404, detail="Payment not found or not a Paystack payment")

        # Check authorization
        if payment.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to verify this payment")

        # Call Paystack verify API
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
        headers = {
            "Authorization": f"Bearer {paystack_secret_key}",
            "Content-Type": "application/json"
        }

        with httpx.Client() as client:
            response = client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=30.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Paystack API error: {response.text}")

        paystack_response = response.json()
        if not paystack_response.get("status"):
            raise HTTPException(status_code=502, detail=f"Paystack verification failed: {paystack_response}")

        data = paystack_response.get("data", {})
        status = data.get("status")
        amount = data.get("amount")  # in kobo

        if status == "success":
            # Verify amount
            expected_amount_kobo = int(payment.amount * 100)
            if amount == expected_amount_kobo:
                # Update payment status
                PaymentService.update_payment_status(
                    db,
                    payment.id,
                    PaymentUpdate(status=PaymentStatus.COMPLETED, transaction_id=reference)
                )
                return {"status": "verified", "payment": payment}
            else:
                return {"status": "amount_mismatch", "expected": expected_amount_kobo, "received": amount}
        else:
            # Update to failed if not already completed
            if payment.status != PaymentStatus.COMPLETED:
                PaymentService.update_payment_status(
                    db,
                    payment.id,
                    PaymentUpdate(status=PaymentStatus.FAILED, transaction_id=reference)
                )
            return {"status": "failed", "payment": payment}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying Paystack payment: {str(e)}")
@router.get("/callback")
def paystack_callback(
    reference: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle Paystack callback redirect after payment.
    Verifies the payment with Paystack and updates status.
    """
    try:
        if not reference:
            raise HTTPException(status_code=400, detail="Reference parameter required")

        # Find payment by reference
        payment = PaymentService.get_payment_by_id(db, reference)
        if not payment or payment.gateway != PaymentGateway.PAYSTACK:
            raise HTTPException(status_code=404, detail="Payment not found or not a Paystack payment")

        # Call Paystack verify API
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
        headers = {
            "Authorization": f"Bearer {paystack_secret_key}",
            "Content-Type": "application/json"
        }

        with httpx.Client() as client:
            response = client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=30.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Paystack API error: {response.text}")

        paystack_response = response.json()
        if not paystack_response.get("status"):
            raise HTTPException(status_code=502, detail=f"Paystack verification failed: {paystack_response}")

        data = paystack_response.get("data", {})
        status = data.get("status")
        amount = data.get("amount")  # in kobo

        if status == "success":
            # Verify amount
            expected_amount_kobo = int(payment.amount * 100)
            if amount == expected_amount_kobo:
                # Update payment status
                PaymentService.update_payment_status(
                    db,
                    payment.id,
                    PaymentUpdate(status=PaymentStatus.COMPLETED, transaction_id=reference)
                )
                return {"status": "success", "message": "Payment verified and completed"}
            else:
                return {"status": "amount_mismatch", "expected": expected_amount_kobo, "received": amount}
        else:
            # Update to failed if not already completed
            if payment.status != PaymentStatus.COMPLETED:
                PaymentService.update_payment_status(
                    db,
                    payment.id,
                    PaymentUpdate(status=PaymentStatus.FAILED, transaction_id=reference)
                )
            return {"status": "failed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Paystack callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing callback: {str(e)}")