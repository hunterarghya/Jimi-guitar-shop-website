"""Product router - API endpoints."""
from fastapi import APIRouter, Depends, Query, File, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core import get_mongo_db
from app.core.security import get_current_user
from app.modules.products.schemas import (
    ProductResponse,
    ProductListResponse,
    ProductFilterRequest,
    CreateProductRequest,
    UpdateProductRequest,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.modules.products.service import ProductService, CategoryService
from app.middleware import AppException
from app.core.imagekit import ImageKitHelper
from typing import Optional, List
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


@router.post("/upload-image", response_model=dict)
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload product image to ImageKit (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can upload product images", 403)

    if not file.content_type.startswith("image/"):
        raise AppException("Only image files are allowed", 400)

    try:
        content = await file.read()
        result = await ImageKitHelper.upload_file(
            file_content=content,
            file_name=file.filename,
            folder="products"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to upload product image: {str(e)}")
        raise AppException(f"Upload failed: {str(e)}", 500)


# Category endpoints
@router.get("/categories/all", response_model=List[CategoryResponse], tags=["categories"])
async def list_categories(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """List all categories."""
    service = CategoryService(db)
    return await service.list_categories()


@router.post("/categories", response_model=CategoryResponse, tags=["categories"])
async def create_category(
    req: CategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create new category (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can create categories", 403)

    service = CategoryService(db)
    return await service.create_category(req)


@router.patch("/categories/{category_id}", response_model=CategoryResponse, tags=["categories"])
async def update_category(
    category_id: str,
    req: CategoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update category (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can update categories", 403)

    service = CategoryService(db)
    return await service.update_category(category_id, req)


@router.delete("/categories/{category_id}", response_model=dict, tags=["categories"])
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete category (admin only)."""
    if not current_user.get("is_admin"):
        raise AppException("Only admins can delete categories", 403)

    service = CategoryService(db)
    return await service.delete_category(category_id)
