"""Order service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from decimal import Decimal
import math
from app.modules.orders.models import Order, OrderStatus, Payment, PaymentStatus
from app.modules.orders.schemas import (
    CreateOrderRequest,
    OrderResponse,
    PaymentResponse,
    OrderItemSchema,
)
from app.middleware import AppException
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class OrderService:
    """Order service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_order(self, user_id: UUID, req: CreateOrderRequest) -> tuple[OrderResponse, dict]:
        """Create order (returns order and razorpay order details)."""
        # Validate home delivery radius
        if req.is_home_delivery:
            distance = self._calculate_distance(
                req.shipping_address.latitude,
                req.shipping_address.longitude,
                self.settings.SHOP_LATITUDE,
                self.settings.SHOP_LONGITUDE,
            )

            if distance > self.settings.SHOP_RADIUS_KM:
                raise AppException(
                    f"Delivery not available. Location is {distance:.1f}km away (max {self.settings.SHOP_RADIUS_KM}km)",
                    400,
                )

        # Calculate totals
        subtotal = sum(Decimal(str(item.price)) * item.quantity for item in req.items)
        tax_amount = subtotal * Decimal("0.18")  # 18% GST
        final_amount = subtotal + tax_amount

        # Create order
        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=float(subtotal),
            tax_amount=float(tax_amount),
            final_amount=float(final_amount),
            items=[item.dict() for item in req.items],
            shipping_address=req.shipping_address.dict(),
            is_home_delivery=req.is_home_delivery,
        )

        self.db.add(order)
        await self.db.flush()

        # Create payment record
        payment = Payment(
            order_id=order.id,
            user_id=user_id,
            amount=float(final_amount),
            status=PaymentStatus.PENDING,
        )

        self.db.add(payment)
        await self.db.commit()

        logger.info(f"Order created: {order.id}")

        # Prepare Razorpay order details
        razorpay_order_data = {
            "amount": int(final_amount * 100),  # Amount in paise
            "currency": "INR",
            "receipt": str(order.id),
            "description": f"Order {order.id}",
        }

        order_response = self._format_order_response(order)
        return order_response, razorpay_order_data

    async def get_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Get order by ID (check ownership)."""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == user_id)
        )
        order = result.scalars().first()

        if not order:
            raise AppException("Order not found", 404)

        return self._format_order_response(order)

    async def list_user_orders(self, user_id: UUID, skip: int = 0, limit: int = 20) -> list[OrderResponse]:
        """List user orders."""
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        orders = result.scalars().all()

        return [self._format_order_response(o) for o in orders]

    async def get_order_payment(self, order_id: UUID) -> PaymentResponse:
        """Get payment for order."""
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        payment = result.scalars().first()

        if not payment:
            raise AppException("Payment not found", 404)

        return self._format_payment_response(payment)

    async def update_payment_razorpay_order(
        self, order_id: UUID, razorpay_order_id: str
    ) -> None:
        """Update payment with Razorpay order ID."""
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        payment = result.scalars().first()

        if not payment:
            raise AppException("Payment not found", 404)

        payment.razorpay_order_id = razorpay_order_id
        await self.db.commit()

    async def verify_payment(
        self, order_id: UUID, razorpay_payment_id: str, razorpay_signature: str
    ) -> PaymentResponse:
        """Verify payment (Razorpay signature verification)."""
        from app.core.security import verify_token
        import hmac
        import hashlib

        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        payment = result.scalars().first()

        if not payment:
            raise AppException("Payment not found", 404)

        # Verify signature
        payload = f"{payment.razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            self.settings.RAZORPAY_KEY_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        if expected_signature != razorpay_signature:
            raise AppException("Invalid payment signature", 401)

        # Update payment
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = PaymentStatus.SUCCESS

        # Update order status
        order = await self.db.execute(select(Order).where(Order.id == order_id))
        order = order.scalars().first()
        order.status = OrderStatus.CONFIRMED

        await self.db.commit()

        logger.info(f"Payment verified for order {order_id}")

        return self._format_payment_response(payment)

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates (Haversine formula)."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth's radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _format_order_response(self, order: Order) -> OrderResponse:
        """Format order to response schema."""
        return OrderResponse(
            id=str(order.id),
            user_id=str(order.user_id),
            status=order.status,
            total_amount=Decimal(str(order.total_amount)),
            discount_amount=Decimal(str(order.discount_amount)),
            tax_amount=Decimal(str(order.tax_amount)),
            final_amount=Decimal(str(order.final_amount)),
            items=[OrderItemSchema(**item) for item in order.items],
            shipping_address=order.shipping_address,
            is_home_delivery=order.is_home_delivery,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def _format_payment_response(self, payment: Payment) -> PaymentResponse:
        """Format payment to response schema."""
        return PaymentResponse(
            id=str(payment.id),
            order_id=str(payment.order_id),
            user_id=str(payment.user_id),
            razorpay_order_id=payment.razorpay_order_id,
            razorpay_payment_id=payment.razorpay_payment_id,
            amount=Decimal(str(payment.amount)),
            currency=payment.currency,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
