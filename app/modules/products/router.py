"""Product router - API endpoints."""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core import get_mongo_db
from app.core.security import get_current_user
from app.modules.products.service import ProductService
from app.modules.products.schemas import (
    ProductResponse,
    ProductListResponse,
    ProductFilterRequest,
    CreateProductRequest,
    UpdateProductRequest,
)
from app.middleware import AppException
from typing import Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    min_rating: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    in_stock: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """List all products with filtering, sorting, and pagination."""
    filters = ProductFilterRequest(
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        search=search,
        brand=brand,
        in_stock=in_stock,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    service = ProductService(db)
    return await service.list_products(filters)


@router.get("/search", response_model=list[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Search products by name and description."""
    if len(q) < 2:
        raise AppException("Search term must be at least 2 characters", 400)

    service = ProductService(db)
    return await service.search_products(q, limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get product details by ID."""
    service = ProductService(db)
    return await service.get_product(product_id)


@router.post("", response_model=ProductResponse)
async def create_product(
    req: CreateProductRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create new product (admin only)."""
    # Verify admin
    if not current_user.get("is_admin"):
        raise AppException("Only admins can create products", 403)

    service = ProductService(db)
    return await service.create_product(req)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    req: UpdateProductRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update product (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can update products", 403)

    service = ProductService(db)
    return await service.update_product(product_id, req)


@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete product (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can delete products", 403)

    service = ProductService(db)
    return await service.delete_product(product_id)
