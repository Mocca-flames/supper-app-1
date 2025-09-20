from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json # Added for json.loads
import os # Added for os.getenv
import httpx # Added for HTTP requests to PayFast API
import hashlib # Added for MD5 signature generation
import urllib.parse # Added for URL encoding
from datetime import datetime # Added for timestamp generation

from ..database import get_db
from ..services.payment_service import PaymentService
from ..schemas.payment_schemas import PaymentCreate, PaymentResponse, PaymentUpdate, RefundCreate, RefundResponse
from ..auth.middleware import get_current_user
from ..schemas.user_schemas import UserResponse
from ..models.payment_models import PaymentType
from ..models.order_models import Order
from ..config import settings # Added for settings

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