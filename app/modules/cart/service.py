"""Cart service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.modules.orders.models import Cart
from app.modules.cart.schemas import CartItem, AddToCartRequest, CartSummary
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)


class CartService:
    """Cart service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        """Get or create cart for user."""
        result = await self.db.execute(select(Cart).where(Cart.user_id == user_id))
        cart = result.scalars().first()

        if not cart:
            cart = Cart(user_id=user_id, items=[])
            self.db.add(cart)
            await self.db.flush()

        return cart

    async def get_cart(self, user_id: UUID) -> dict:
        """Get user cart."""
        cart = await self.get_or_create_cart(user_id)

        total_amount = sum(item.get("price", 0) * item.get("quantity", 0) for item in cart.items)

        return {
            "id": str(cart.id),
            "user_id": str(cart.user_id),
            "items": cart.items,
            "total_items": len(cart.items),
            "total_amount": total_amount,
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
        }

    async def add_to_cart(self, user_id: UUID, req: AddToCartRequest, product_price: float) -> dict:
        """Add item to cart."""
        # Validate quantity
        if req.quantity > 10:
            raise AppException("Maximum 10 items per product", 400)

        cart = await self.get_or_create_cart(user_id)

        # Check if item already in cart
        existing_item = None
        for item in cart.items:
            if item["product_id"] == req.product_id:
                existing_item = item
                break

        if existing_item:
            # Update quantity
            new_qty = existing_item["quantity"] + req.quantity
            if new_qty > 10:
                raise AppException(f"Maximum 10 items allowed. Current: {existing_item['quantity']}", 400)
            existing_item["quantity"] = new_qty
        else:
            # Add new item
            if len(cart.items) >= 10:
                raise AppException("Maximum 10 different products in cart", 400)
            cart.items.append({
                "product_id": req.product_id,
                "quantity": req.quantity,
                "price": product_price,
            })

        await self.db.commit()
        logger.info(f"Item added to cart for user {user_id}: {req.product_id}")

        return await self.get_cart(user_id)

    async def update_cart_item(self, user_id: UUID, product_id: str, quantity: int) -> dict:
        """Update cart item quantity."""
        if quantity < 1 or quantity > 10:
            raise AppException("Quantity must be between 1 and 10", 400)

        cart = await self.get_or_create_cart(user_id)

        for item in cart.items:
            if item["product_id"] == product_id:
                item["quantity"] = quantity
                await self.db.commit()
                logger.info(f"Cart item updated for user {user_id}: {product_id}")
                return await self.get_cart(user_id)

        raise AppException("Item not in cart", 404)

    async def remove_from_cart(self, user_id: UUID, product_id: str) -> dict:
        """Remove item from cart."""
        cart = await self.get_or_create_cart(user_id)

        original_length = len(cart.items)
        cart.items = [item for item in cart.items if item["product_id"] != product_id]

        if len(cart.items) == original_length:
            raise AppException("Item not in cart", 404)

        await self.db.commit()
        logger.info(f"Item removed from cart for user {user_id}: {product_id}")

        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: UUID) -> dict:
        """Clear user cart."""
        cart = await self.get_or_create_cart(user_id)
        cart.items = []
        await self.db.commit()

        logger.info(f"Cart cleared for user {user_id}")
        return {"message": "Cart cleared"}
