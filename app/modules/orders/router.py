"""Order and payment router - API endpoints."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core import get_db, get_mongo_db
from app.core.security import get_current_user
from app.modules.orders.service import OrderService
from app.modules.orders.schemas import (
    CreateOrderRequest,
    OrderResponse,
    PaymentResponse,
    RazorpayWebhook,
    VerifyPaymentRequest,
    CheckDeliveryRequest,
    CheckDeliveryResponse,
)
from app.modules.products.service import ProductService
from app.modules.cart.service import CartService
from app.middleware import AppException
from uuid import UUID
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(tags=["orders", "payments"])


@router.post("/api/v1/orders", response_model=dict)
async def create_order(
    req: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create order and get Razorpay order details."""
    user_id = UUID(current_user["sub"])

    # Verify product prices match and reserve stock
    product_service = ProductService(mongo_db)
    for item in req.items:
        product = await product_service.get_product(item.product_id)
        if product.price != item.price:
            raise AppException("Product price changed. Please refresh cart.", 400)

    # Reserve stock for all items
    stock_reserve = {item.product_id: item.quantity for item in req.items}
    await product_service.bulk_reserve_stock(stock_reserve)

    # Create order
    order_service = OrderService(db, mongo_db)
    order_response, razorpay_order_data = await order_service.create_order(user_id, req)

    # Clear cart
    cart_service = CartService(db)
    await cart_service.clear_cart(user_id)

    # In production, create Razorpay order here
    # For now, return mock data
    return {
        "order": order_response,
        "razorpay_order": {
            "id": "order_mock_123456",
            "amount": razorpay_order_data["amount"],
            "currency": razorpay_order_data["currency"],
            "key_id": "xxx",  # Replace with actual key in production
        },
    }


@router.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get order details."""
    try:
        oid = UUID(order_id)
    except ValueError:
        raise AppException("Invalid order ID", 400)

    order_service = OrderService(db)
    return await order_service.get_order(oid, UUID(current_user["sub"]))


@router.post("/api/v1/orders/check-delivery", response_model=CheckDeliveryResponse)
async def check_delivery(
    req: CheckDeliveryRequest,
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    db: AsyncSession = Depends(get_db),
):
    """Check if location is within delivery radius."""
    order_service = OrderService(db, mongo_db)
    result = await order_service.check_delivery_radius(req.latitude, req.longitude)
    return CheckDeliveryResponse(**result)


@router.get("/api/v1/orders")
async def list_orders(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user orders."""
    order_service = OrderService(db)
    orders = await order_service.list_user_orders(UUID(current_user["sub"]))
    return {"orders": orders}


@router.post("/api/v1/payments/verify", response_model=PaymentResponse)
async def verify_payment(
    req: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify Razorpay payment."""
    # Extract order ID from Razorpay order ID
    # In production, store order_id with razorpay_order_id during order creation
    # For now, derive it or require it in request

    order_service = OrderService(db)
    # This needs order_id - we need to track it
    raise AppException("Payment verification requires order ID in request", 400)


@router.post("/api/v1/payments/razorpay-webhook")
async def razorpay_webhook(
    payload: dict,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Razorpay webhook."""
    import hmac
    import hashlib

    from app.core.config import get_settings

    settings = get_settings()

    # Verify signature
    payload_str = json.dumps(payload, separators=(",", ":"))
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        payload_str.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected_signature != x_razorpay_signature:
        logger.warning("Invalid webhook signature")
        raise AppException("Invalid signature", 401)

    # Handle webhook events
    event = payload.get("event")
    entity = payload.get("payload", {}).get("payment", {})

    if event == "payment.authorized":
        razorpay_payment_id = entity.get("id")
        razorpay_order_id = entity.get("order_id")

        logger.info(f"Payment authorized: {razorpay_payment_id}")

        # Update payment status in DB
        # This requires a query by razorpay_order_id or razorpay_payment_id

    elif event == "payment.failed":
        razorpay_payment_id = entity.get("id")
        logger.warning(f"Payment failed: {razorpay_payment_id}")

        # Update payment status to failed

    return {"status": "ok"}


@router.get("/api/v1/payments/{order_id}", response_model=PaymentResponse)
async def get_payment(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment for order."""
    try:
        oid = UUID(order_id)
    except ValueError:
        raise AppException("Invalid order ID", 400)

    order_service = OrderService(db)
    return await order_service.get_order_payment(oid)
