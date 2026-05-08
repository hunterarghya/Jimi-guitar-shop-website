"""Product service - business logic."""
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.modules.products.repository import ProductRepository, CategoryRepository
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
from app.middleware import AppException
import logging

logger = logging.getLogger(__name__)


class ProductService:
    """Product service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = ProductRepository(db)

    async def create_product(self, req: CreateProductRequest) -> ProductResponse:
        """Create new product (admin only)."""
        # Generate SKU if not provided
        sku = req.sku or f"{req.category.upper()}-{int(datetime.now().timestamp())}"
        
        # Check if SKU already exists
        if req.sku:
            existing = await self.repository.get_by_sku(sku)
            if existing:
                raise AppException(f"Product with SKU {sku} already exists", 409)

        # Prepare product data
        product_data = {
            "name": req.name,
            "description": req.description or f"Product: {req.name}",
            "category": req.category,
            "price": float(req.price),
            "stock": req.stock_quantity,
            "sku": sku,
            "images": [img.model_dump() if hasattr(img, 'model_dump') else img for img in req.images] if req.images else [],
            "specifications": [spec.model_dump() if hasattr(spec, 'model_dump') else spec for spec in req.specifications] if req.specifications else [],
            "brand": req.brand,
            "warranty_months": req.warranty_months,
            "weight_kg": req.weight_kg,
        }

        # Create product
        product_id = await self.repository.create(product_data)
        logger.info(f"Product created: {product_id}")

        # Retrieve and return
        product = await self.repository.get_by_id(product_id)
        return self._format_response(product)

    async def get_product(self, product_id: str) -> ProductResponse:
        """Get product by ID."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise AppException("Product not found", 404)

        return self._format_response(product)

    async def update_product(self, product_id: str, req: UpdateProductRequest) -> ProductResponse:
        """Update product (admin only)."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise AppException("Product not found", 404)

        # Prepare update data
        update_data = {}
        if req.name:
            update_data["name"] = req.name
        if req.description:
            update_data["description"] = req.description
        if req.category:
            update_data["category"] = req.category
        if req.price:
            update_data["price"] = float(req.price)
        if req.stock is not None:
            update_data["stock"] = req.stock
        if req.images:
            update_data["images"] = [img.model_dump() if hasattr(img, 'model_dump') else img for img in req.images]
        if req.specifications:
            update_data["specifications"] = [spec.model_dump() if hasattr(spec, 'model_dump') else spec for spec in req.specifications]
        if req.brand:
            update_data["brand"] = req.brand
        if req.warranty_months:
            update_data["warranty_months"] = req.warranty_months
        if req.weight_kg:
            update_data["weight_kg"] = req.weight_kg

        # Update product
        success = await self.repository.update(product_id, update_data)
        if not success:
            raise AppException("Failed to update product", 500)

        logger.info(f"Product updated: {product_id}")

        # Retrieve and return
        product = await self.repository.get_by_id(product_id)
        return self._format_response(product)

    async def delete_product(self, product_id: str) -> dict:
        """Delete product (soft delete)."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise AppException("Product not found", 404)

        success = await self.repository.soft_delete(product_id)
        if not success:
            raise AppException("Failed to delete product", 500)

        logger.info(f"Product deleted: {product_id}")
        return {"message": "Product deleted successfully"}

    async def list_products(self, filters: ProductFilterRequest) -> ProductListResponse:
        """List products with filters."""
        products, total = await self.repository.list_products(filters)

        formatted_products = [self._format_response(p) for p in products]

        total_pages = (total + filters.page_size - 1) // filters.page_size

        return ProductListResponse(
            items=formatted_products,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    async def search_products(self, search_term: str, limit: int = 10) -> List[ProductResponse]:
        """Search products by text."""
        products = await self.repository.search_by_text(search_term, limit)
        return [self._format_response(p) for p in products]

    async def update_stock(self, product_id: str, quantity_change: int) -> dict:
        """Update product stock."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise AppException("Product not found", 404)

        # Check if stock would go negative
        new_stock = product.get("stock", 0) + quantity_change
        if new_stock < 0:
            raise AppException(f"Insufficient stock. Current: {product.get('stock', 0)}", 400)

        success = await self.repository.update_stock(product_id, quantity_change)
        if not success:
            raise AppException("Failed to update stock", 500)

        updated_product = await self.repository.get_by_id(product_id)
        return {
            "product_id": product_id,
            "new_stock": updated_product.get("stock", 0),
        }

    async def bulk_reserve_stock(self, items: dict[str, int]) -> dict:
        """Reserve stock for multiple products (for orders)."""
        # First, verify all products have sufficient stock
        for product_id, quantity in items.items():
            product = await self.repository.get_by_id(product_id)
            if not product:
                raise AppException(f"Product {product_id} not found", 404)

            current_stock = product.get("stock", 0)
            if current_stock < quantity:
                raise AppException(
                    f"Insufficient stock for {product.get('name')}. Available: {current_stock}, Requested: {quantity}",
                    400,
                )

        # Reserve stock
        success = await self.repository.bulk_update_stock(
            {pid: -qty for pid, qty in items.items()}
        )

        if not success and items:
            raise AppException("Failed to reserve stock", 500)

        logger.info(f"Stock reserved for order: {items}")
        return {"message": "Stock reserved successfully"}

    def _format_response(self, product: dict) -> ProductResponse:
        """Format MongoDB document to response schema."""
        return ProductResponse(
            id=str(product["_id"]),
            name=product.get("name"),
            description=product.get("description"),
            category=product.get("category"),
            price=Decimal(str(product.get("price", 0))),
            stock=product.get("stock", 0),
            sku=product.get("sku"),
            images=product.get("images", []),
            specifications=product.get("specifications", []),
            brand=product.get("brand"),
            warranty_months=product.get("warranty_months"),
            weight_kg=product.get("weight_kg"),
            rating=product.get("rating", 0.0),
            reviews_count=product.get("reviews_count", 0),
            created_at=product.get("created_at"),
            updated_at=product.get("updated_at"),
        )


class CategoryService:
    """Category service."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = CategoryRepository(db)

    async def create_category(self, req: CategoryCreate) -> CategoryResponse:
        """Create new category."""
        category_data = {
            "name": req.name,
            "description": req.description,
        }
        category_id = await self.repository.create(category_data)
        doc = await self.repository.get_by_id(category_id)
        return self._format_response(doc)

    async def list_categories(self) -> List[CategoryResponse]:
        """List all categories."""
        categories = await self.repository.get_all()
        return [self._format_response(c) for c in categories]

    async def update_category(self, category_id: str, req: CategoryUpdate) -> CategoryResponse:
        """Update category."""
        update_data = {}
        if req.name:
            update_data["name"] = req.name
        if req.description is not None:
            update_data["description"] = req.description

        success = await self.repository.update(category_id, update_data)
        if not success:
            raise AppException("Failed to update category or category not found", 404)

        doc = await self.repository.get_by_id(category_id)
        return self._format_response(doc)

    async def delete_category(self, category_id: str) -> dict:
        """Delete category."""
        success = await self.repository.delete(category_id)
        if not success:
            raise AppException("Failed to delete category or category not found", 404)
        return {"message": "Category deleted successfully"}

    def _format_response(self, category: dict) -> CategoryResponse:
        """Format MongoDB document to response schema."""
        return CategoryResponse(
            id=str(category["_id"]),
            name=category.get("name"),
            description=category.get("description"),
            created_at=category.get("created_at"),
            updated_at=category.get("updated_at"),
        )
