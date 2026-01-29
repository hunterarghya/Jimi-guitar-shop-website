"""Product schemas for MongoDB."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ProductImage(BaseModel):
    """Product image metadata."""
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False


class ProductSpecification(BaseModel):
    """Product specification."""
    key: str
    value: str


class CreateProductRequest(BaseModel):
    """Create product request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=5000)
    category: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    sku: Optional[str] = None
    images: List[ProductImage] = Field(default_factory=list)
    specifications: List[ProductSpecification] = Field(default_factory=list)
    brand: Optional[str] = None
    warranty_months: Optional[int] = None
    weight_kg: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Fender Stratocaster",
                "description": "Classic electric guitar with 3 single-coil pickups",
                "category": "Electric Guitar",
                "price": 799.99,
                "stock": 10,
                "sku": "FEND-STRAT-001",
                "brand": "Fender",
                "warranty_months": 24,
                "weight_kg": 3.6,
                "images": [
                    {
                        "url": "https://imagekit.io/...",
                        "alt_text": "Fender Stratocaster front view",
                        "is_primary": True,
                    }
                ],
                "specifications": [
                    {"key": "Type", "value": "Electric Guitar"},
                    {"key": "Body Material", "value": "Alder"},
                ],
            }
        }


class UpdateProductRequest(BaseModel):
    """Update product request."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    images: Optional[List[ProductImage]] = None
    specifications: Optional[List[ProductSpecification]] = None
    brand: Optional[str] = None
    warranty_months: Optional[int] = None
    weight_kg: Optional[float] = None


class ProductResponse(BaseModel):
    """Product response."""
    id: str = Field(alias="_id")
    name: str
    description: str
    category: str
    price: Decimal
    stock: int
    sku: str
    images: List[ProductImage]
    specifications: List[ProductSpecification]
    brand: Optional[str] = None
    warranty_months: Optional[int] = None
    weight_kg: Optional[float] = None
    rating: float = 0.0
    reviews_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class ProductListResponse(BaseModel):
    """Product list response with pagination."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductFilterRequest(BaseModel):
    """Product filter request."""
    category: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    search: Optional[str] = None
    brand: Optional[str] = None
    in_stock: Optional[bool] = None
    sort_by: Optional[str] = Field("created_at", pattern="^(price|rating|created_at|name)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Electric Guitar",
                "min_price": 500,
                "max_price": 2000,
                "min_rating": 4.0,
                "in_stock": True,
                "sort_by": "price",
                "sort_order": "asc",
                "page": 1,
                "page_size": 20,
            }
        }
