"""Order and payment models for PostgreSQL."""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    UUID,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from enum import Enum as PyEnum
import uuid

Base = declarative_base()


class OrderStatus(str, PyEnum):
    """Order status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, PyEnum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    """Order model."""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Order details
    status = Column(String(20), default=OrderStatus.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    final_amount = Column(Float, nullable=False)
    
    # Items (stored as JSONB for flexibility)
    items = Column(JSONB, nullable=False)  # [{product_id, quantity, price}, ...]
    
    # Delivery
    shipping_address = Column(JSONB, nullable=False)
    delivery_radius_km = Column(Float, nullable=True)
    is_home_delivery = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order {self.id}>"


class Payment(Base):
    """Payment model."""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment provider details
    razorpay_order_id = Column(String(255), nullable=True, index=True)
    razorpay_payment_id = Column(String(255), nullable=True, unique=True, index=True)
    razorpay_signature = Column(String(255), nullable=True)
    
    # Amount
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    
    # Status
    status = Column(String(20), default=PaymentStatus.PENDING, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_razorpay_order_id", "razorpay_order_id"),
    )

    def __repr__(self) -> str:
        return f"<Payment {self.id}>"


class Cart(Base):
    """Shopping cart model."""

    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Cart items stored as JSONB
    items = Column(JSONB, nullable=False, default=lambda: [])  # [{product_id, quantity}, ...]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Cart {self.user_id}>"
