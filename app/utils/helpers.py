import random
from enum import Enum
from typing import Optional, Dict, Any

class MockPaymentStatus(str, Enum):
    """Mock payment statuses to simulate gateway responses"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"

class MockPaymentProcessor:
    """
    Mock payment processor to simulate real-world payment gateway behavior.
    Randomly accepts or declines payments for testing purposes.
    """

    @staticmethod
    def process_payment(amount: float, currency: str = "ZAR", **kwargs) -> Dict[str, Any]:
        """
        Simulate payment processing with random success/failure.

        Args:
            amount: Payment amount
            currency: Currency code (default: ZAR)
            **kwargs: Additional payment details

        Returns:
            Dictionary with mock transaction result including:
            - status: SUCCESS or FAILURE
            - transaction_id: Mock transaction ID
            - message: Result message
            - raw_response: Additional mock details
        """
        # Randomly determine if payment succeeds or fails
        # 80% success rate for testing
        success = random.random() < 0.8

        transaction_id = f"mock_tx_{int(random.random() * 1000000)}"

        if success:
            return {
                "status": MockPaymentStatus.SUCCESS,
                "transaction_id": transaction_id,
                "message": "Payment processed successfully",
                "raw_response": {
                    "gateway": "mock_gateway",
                    "amount": amount,
                    "currency": currency,
                    "approval_code": f"APPROVED_{transaction_id}"
                }
            }
        else:
            return {
                "status": MockPaymentStatus.FAILURE,
                "transaction_id": transaction_id,
                "message": "Payment declined by mock gateway",
                "raw_response": {
                    "gateway": "mock_gateway",
                    "amount": amount,
                    "currency": currency,
                    "decline_reason": random.choice([
                        "Insufficient funds",
                        "Invalid card details",
                        "Bank rejection",
                        "Fraud detection"
                    ])
                }
            }

    @staticmethod
    def simulate_refund(transaction_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Simulate payment refund processing.

        Args:
            transaction_id: Original transaction ID
            amount: Refund amount (None for full refund)

        Returns:
            Dictionary with mock refund result
        """
        # 90% success rate for refunds
        success = random.random() < 0.9

        refund_id = f"mock_refund_{int(random.random() * 1000000)}"

        if success:
            return {
                "status": MockPaymentStatus.SUCCESS,
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "message": "Refund processed successfully",
                "raw_response": {
                    "gateway": "mock_gateway",
                    "amount": amount,
                    "refund_approval": f"REFUNDED_{refund_id}"
                }
            }
        else:
            return {
                "status": MockPaymentStatus.FAILURE,
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "message": "Refund failed",
                "raw_response": {
                    "gateway": "mock_gateway",
                    "amount": amount,
                    "failure_reason": random.choice([
                        "Original transaction not found",
                        "Refund amount exceeds available balance",
                        "Bank rejection",
                        "Technical error"
                    ])
                }
            }
