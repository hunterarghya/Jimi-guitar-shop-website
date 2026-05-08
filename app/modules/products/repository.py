"""Product repository - MongoDB data access."""
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from app.modules.products.schemas import ProductFilterRequest
import logging

logger = logging.getLogger(__name__)


class ProductRepository:
    """Product repository for MongoDB operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection: AsyncIOMotorCollection = db["products"]

    async def init_indexes(self) -> None:
        """Initialize MongoDB indexes."""
        await self.collection.create_index("sku", unique=True)
        await self.collection.create_index("category")
        await self.collection.create_index("price")
        await self.collection.create_index("rating")
        await self.collection.create_index("stock")
        await self.collection.create_index("brand")
        await self.collection.create_index([("name", "text"), ("description", "text")])
        logger.info("Product indexes created")

    async def create(self, product_data: Dict[str, Any]) -> str:
        """Create product."""
        product_data["created_at"] = datetime.now(timezone.utc)
        product_data["updated_at"] = datetime.now(timezone.utc)
        product_data["rating"] = 0.0
        product_data["reviews_count"] = 0
        product_data["is_deleted"] = False

        result = await self.collection.insert_one(product_data)
        return str(result.inserted_id)

    async def get_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product by ID."""
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(product_id),
                "is_deleted": False,
            })
            return doc
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None

    async def get_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product by SKU."""
        return await self.collection.find_one({
            "sku": sku,
            "is_deleted": False,
        })

    async def update(self, product_id: str, update_data: Dict[str, Any]) -> bool:
        """Update product."""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)

            result = await self.collection.update_one(
                {
                    "_id": ObjectId(product_id),
                    "is_deleted": False,
                },
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return False

    async def soft_delete(self, product_id: str) -> bool:
        """Soft delete product."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(product_id)},
                {
                    "$set": {
                        "is_deleted": True,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return False

    async def list_products(self, filters: ProductFilterRequest) -> tuple[List[Dict], int]:
        """List products with filters and pagination."""
        query: Dict[str, Any] = {"is_deleted": False}

        # Filter by category
        if filters.category:
            query["category"] = filters.category

        # Filter by price range
        if filters.min_price or filters.max_price:
            price_query = {}
            if filters.min_price:
                price_query["$gte"] = float(filters.min_price)
            if filters.max_price:
                price_query["$lte"] = float(filters.max_price)
            query["price"] = price_query

        # Filter by rating
        if filters.min_rating:
            query["rating"] = {"$gte": filters.min_rating}

        # Filter by brand
        if filters.brand:
            query["brand"] = filters.brand

        # Filter by stock
        if filters.in_stock is not None:
            if filters.in_stock:
                query["stock"] = {"$gt": 0}
            else:
                query["stock"] = 0

        # Text search
        if filters.search:
            query["$text"] = {"$search": filters.search}

        # Get total count
        total = await self.collection.count_documents(query)

        # Sort
        sort_field = filters.sort_by or "created_at"
        sort_order = 1 if filters.sort_order == "asc" else -1

        # Handle text search score
        if filters.search:
            sort_spec = [
                ("score", {"$meta": "textScore"}),
                (sort_field, sort_order),
            ]
        else:
            sort_spec = [(sort_field, sort_order)]

        # Pagination
        skip = (filters.page - 1) * filters.page_size
        
        # Execute query
        cursor = self.collection.find(query)
        
        if filters.search:
            cursor = cursor.add_option(32)  # Allow disk use for text search
        
        products = await cursor.sort(sort_spec).skip(skip).limit(filters.page_size).to_list(length=None)

        return products, total

    async def update_stock(self, product_id: str, quantity_change: int) -> bool:
        """Update product stock."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(product_id), "is_deleted": False},
                {
                    "$inc": {"stock": quantity_change},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating stock for {product_id}: {str(e)}")
            return False

    async def bulk_update_stock(self, updates: Dict[str, int]) -> bool:
        """Bulk update stock for multiple products."""
        try:
            operations = []
            for product_id, quantity_change in updates.items():
                operations.append(
                    {
                        "update_one": {
                            "filter": {"_id": ObjectId(product_id), "is_deleted": False},
                            "update": {
                                "$inc": {"stock": quantity_change},
                                "$set": {"updated_at": datetime.now(timezone.utc)},
                            },
                        }
                    }
                )

            if operations:
                result = await self.collection.bulk_write(operations)
                return result.modified_count > 0

            return False
        except Exception as e:
            logger.error(f"Error bulk updating stock: {str(e)}")
            return False

    async def update_rating(self, product_id: str, rating: float, increment_count: bool = True) -> bool:
        """Update product rating."""
        try:
            update_data = {
                "rating": rating,
                "updated_at": datetime.now(timezone.utc),
            }

            inc_data = {}
            if increment_count:
                inc_data["reviews_count"] = 1

            result = await self.collection.update_one(
                {"_id": ObjectId(product_id), "is_deleted": False},
                {
                    "$set": update_data,
                    "$inc": inc_data if inc_data else {"$set": {}},
                },
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating rating for {product_id}: {str(e)}")
            return False

    async def search_by_text(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search products by text."""
        try:
            products = await self.collection.find(
                {
                    "$text": {"$search": search_term},
                    "is_deleted": False,
                },
                {"score": {"$meta": "textScore"}},
            ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(length=None)

            return products
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []


class CategoryRepository:
    """Category repository for MongoDB operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection: AsyncIOMotorCollection = db["categories"]

    async def init_indexes(self) -> None:
        """Initialize MongoDB indexes."""
        await self.collection.create_index("name", unique=True)
        logger.info("Category indexes created")

    async def create(self, category_data: Dict[str, Any]) -> str:
        """Create category."""
        category_data["created_at"] = datetime.now(timezone.utc)
        category_data["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.insert_one(category_data)
        return str(result.inserted_id)

    async def get_all(self) -> List[Dict]:
        """Get all categories."""
        return await self.collection.find().sort("name", 1).to_list(length=None)

    async def get_by_id(self, category_id: str) -> Optional[Dict]:
        """Get category by ID."""
        try:
            return await self.collection.find_one({"_id": ObjectId(category_id)})
        except Exception:
            return None

    async def update(self, category_id: str, update_data: Dict[str, Any]) -> bool:
        """Update category."""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)
            result = await self.collection.update_one(
                {"_id": ObjectId(category_id)},
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {str(e)}")
            return False

    async def delete(self, category_id: str) -> bool:
        """Delete category (hard delete)."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(category_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {str(e)}")
            return False
