"""Cart router - API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_db
from app.core.security import get_current_user
from app.modules.cart.service import CartService
from app.modules.cart.schemas import AddToCartRequest, UpdateCartItemRequest
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cart", tags=["cart"])


@router.get("")
async def get_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user cart."""
    from uuid import UUID
    service = CartService(db)
    return await service.get_cart(UUID(current_user["sub"]))


@router.post("/items")
async def add_to_cart(
    req: AddToCartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add item to cart."""
    from uuid import UUID
    from app.modules.products.service import ProductService
    from app.core import get_mongo_db

    # Verify product exists and get price
    mongo_db = get_mongo_db()
    product_service = ProductService(mongo_db)
    product = await product_service.get_product(req.product_id)

    service = CartService(db)
    return await service.add_to_cart(UUID(current_user["sub"]), req, float(product.price))


@router.put("/items/{product_id}")
async def update_cart_item(
    product_id: str,
    req: UpdateCartItemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update cart item quantity."""
    from uuid import UUID
    service = CartService(db)
    return await service.update_cart_item(UUID(current_user["sub"]), product_id, req.quantity)


@router.delete("/items/{product_id}")
async def remove_from_cart(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove item from cart."""
    from uuid import UUID
    service = CartService(db)
    return await service.remove_from_cart(UUID(current_user["sub"]), product_id)


@router.delete("")
async def clear_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear cart."""
    from uuid import UUID
    service = CartService(db)
    return await service.clear_cart(UUID(current_user["sub"]))
