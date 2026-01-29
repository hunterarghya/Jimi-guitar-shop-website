"""Cart schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItem(BaseModel):
    """Cart item."""
    product_id: str
    quantity: int = Field(..., ge=1, le=10)
    price: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439011",
                "quantity": 2,
                "price": 799.99,
            }
        }


class AddToCartRequest(BaseModel):
    """Add to cart request."""
    product_id: str
    quantity: int = Field(1, ge=1, le=10)


class UpdateCartItemRequest(BaseModel):
    """Update cart item request."""
    quantity: int = Field(..., ge=1, le=10)


class CartResponse(BaseModel):
    """Cart response."""
    id: str
    user_id: str
    items: List[CartItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """Cart summary."""
    total_items: int
    total_amount: float
    items: List[CartItem]
