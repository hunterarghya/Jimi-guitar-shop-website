"""Payments repository - Razorpay integration."""
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class RazorpayRepository:
    """Razorpay payment gateway integration."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.razorpay.com/v1"
        self.auth = (self.settings.RAZORPAY_KEY_ID, self.settings.RAZORPAY_KEY_SECRET)

    async def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str = None,
        description: str = None,
        notes: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Create Razorpay order."""
        payload = {
            "amount": amount,  # in paise
            "currency": currency,
            "receipt": receipt,
            "description": description,
        }

        if notes:
            payload["notes"] = notes

        try:
            response = requests.post(
                f"{self.base_url}/orders",
                json=payload,
                auth=self.auth,
                timeout=10,
            )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise

    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from Razorpay."""
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                auth=self.auth,
                timeout=10,
            )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Razorpay payment fetch failed: {str(e)}")
            raise

    async def capture_payment(
        self,
        payment_id: str,
        amount: int,
    ) -> Dict[str, Any]:
        """Capture authorized payment."""
        payload = {"amount": amount}

        try:
            response = requests.post(
                f"{self.base_url}/payments/{payment_id}/capture",
                json=payload,
                auth=self.auth,
                timeout=10,
            )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Razorpay payment capture failed: {str(e)}")
            raise

    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        notes: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Refund payment (full or partial)."""
        payload = {}

        if amount:
            payload["amount"] = amount

        if notes:
            payload["notes"] = notes

        try:
            response = requests.post(
                f"{self.base_url}/payments/{payment_id}/refund",
                json=payload,
                auth=self.auth,
                timeout=10,
            )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Razorpay refund failed: {str(e)}")
            raise

    def verify_webhook_signature(
        self,
        webhook_body: str,
        webhook_signature: str,
    ) -> bool:
        """Verify Razorpay webhook signature."""
        expected_signature = hmac.new(
            self.settings.RAZORPAY_KEY_SECRET.encode(),
            webhook_body.encode(),
            hashlib.sha256,
        ).hexdigest()

        return expected_signature == webhook_signature

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify payment signature from payment gateway response."""
        payload = f"{razorpay_order_id}|{razorpay_payment_id}"

        expected_signature = hmac.new(
            self.settings.RAZORPAY_KEY_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return expected_signature == razorpay_signature
