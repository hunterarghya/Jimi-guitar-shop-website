"""Order and payment schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderItemSchema(BaseModel):
    """Order item."""
    product_id: str
    quantity: int
    price: Decimal


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class ShippingAddress(BaseModel):
    """Shipping address."""
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "IN"
    latitude: float
    longitude: float
    phone: str

    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Music Street",
                "city": "Delhi",
                "state": "Delhi",
                "postal_code": "110001",
                "country": "IN",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "phone": "+919876543210",
            }
        }


class CreateOrderRequest(BaseModel):
    """Create order request."""
    items: List[OrderItemSchema]
    shipping_address: ShippingAddress
    is_home_delivery: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 1,
                        "price": 799.99,
                    }
                ],
                "shipping_address": {
                    "street": "123 Music Street",
                    "city": "Delhi",
                    "state": "Delhi",
                    "postal_code": "110001",
                    "country": "IN",
                    "latitude": 28.6139,
                    "longitude": 77.2090,
                    "phone": "+919876543210",
                },
                "is_home_delivery": True,
            }
        }


class RazorpayWebhook(BaseModel):
    """Razorpay webhook payload."""
    event: str
    created_at: int
    entity: dict


class VerifyPaymentRequest(BaseModel):
    """Verify payment request."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderResponse(BaseModel):
    """Order response."""
    id: str
    user_id: str
    status: OrderStatus
    total_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    final_amount: Decimal
    items: List[OrderItemSchema]
    shipping_address: dict
    is_home_delivery: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response."""
    id: str
    order_id: str
    user_id: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckDeliveryRequest(BaseModel):
    """Delivery radius check request."""
    latitude: float = Field(..., description="User's latitude")
    longitude: float = Field(..., description="User's longitude")


class CheckDeliveryResponse(BaseModel):
    """Delivery radius check response."""
    is_deliverable: bool = Field(..., description="Is the location within delivery radius")
    distance_km: float = Field(..., description="Distance from shop in KM")
    shop_radius_km: float = Field(..., description="Shop's configured delivery radius")
    message: str = Field(..., description="Status message")
