"""Admin module repository."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class AdminRepository:
    """Admin repository for database operations."""

    def __init__(self, db: AsyncSession, mongo_db: AsyncIOMotorDatabase):
        """Initialize repository."""
        self.db = db
        self.mongo_db = mongo_db

    async def get_revenue_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue metrics for last N days."""
        from app.modules.orders.models import Order, Payment
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Query payments
            query = select(
                func.count(Payment.id).label("total_transactions"),
                func.sum(Payment.amount).label("total_revenue"),
            ).where(Payment.created_at >= start_date)
            
            result = await self.db.execute(query)
            row = result.first()
            
            total_transactions = row[0] or 0
            total_revenue = float(row[1] or 0)
            
            # Query orders
            orders_query = select(
                func.count(Order.id).label("total_orders"),
                func.sum(
                    func.cast(Order.total_amount, type_=float)
                ).label("orders_revenue"),
            ).where(Order.created_at >= start_date)
            
            result = await self.db.execute(orders_query)
            row = result.first()
            
            total_orders = row[0] or 0
            
            # Get order status counts
            status_query = select(
                Order.status,
                func.count(Order.id).label("count"),
            ).where(Order.created_at >= start_date).group_by(Order.status)
            
            result = await self.db.execute(status_query)
            status_counts = {row[0]: row[1] for row in result.fetchall()}
            
            successful_orders = status_counts.get("completed", 0)
            pending_orders = status_counts.get("pending", 0)
            cancelled_orders = status_counts.get("cancelled", 0)
            
            average_order_value = (
                total_revenue / total_orders if total_orders > 0 else 0
            )
            
            return {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "total_transactions": total_transactions,
                "average_order_value": round(average_order_value, 2),
                "successful_orders": successful_orders,
                "pending_orders": pending_orders,
                "cancelled_orders": cancelled_orders,
            }
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {str(e)}")
            return {
                "total_revenue": 0.0,
                "total_orders": 0,
                "total_transactions": 0,
                "average_order_value": 0.0,
                "successful_orders": 0,
                "pending_orders": 0,
                "cancelled_orders": 0,
            }

    async def get_top_selling_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling products."""
        from app.modules.orders.models import Order
        
        try:
            # Aggregate sales from orders
            pipeline = [
                {"$unwind": "$items"},
                {
                    "$group": {
                        "_id": "$items.product_id",
                        "sale_count": {"$sum": "$items.quantity"},
                        "revenue": {
                            "$sum": {
                                "$multiply": [
                                    "$items.price",
                                    "$items.quantity"
                                ]
                            }
                        },
                    }
                },
                {"$sort": {"sale_count": -1}},
                {"$limit": limit},
            ]
            
            # We'll fetch from MongoDB products collection
            products_col = self.mongo_db["products"]
            
            result = []
            async for item in products_col.aggregate(pipeline):
                result.append({
                    "product_id": str(item.get("_id")),
                    "sale_count": item.get("sale_count", 0),
                    "revenue": round(item.get("revenue", 0), 2),
                })
            
            # Fetch product details and ratings
            for item in result:
                product = await products_col.find_one(
                    {"_id": item["product_id"]}
                )
                if product:
                    item["name"] = product.get("name", "Unknown")
                    item["rating"] = product.get("rating", 0)
            
            return result
        except Exception as e:
            logger.error(f"Error getting top selling products: {str(e)}")
            return []

    async def get_pending_deliveries_count(self) -> int:
        """Get pending deliveries count."""
        from app.modules.orders.models import Order
        
        try:
            query = select(
                func.count(Order.id)
            ).where(Order.status == "pending")
            
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting pending deliveries: {str(e)}")
            return 0

    async def get_total_users(self) -> int:
        """Get total users count."""
        from app.modules.users.models import User
        
        try:
            query = select(func.count(User.id)).where(User.is_deleted == False)
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total users: {str(e)}")
            return 0

    async def get_new_users_today(self) -> int:
        """Get new users created today."""
        from app.modules.users.models import User
        
        try:
            today = datetime.utcnow().date()
            query = select(
                func.count(User.id)
            ).where(
                and_(
                    func.date(User.created_at) == today,
                    User.is_deleted == False,
                )
            )
            result = await self.db.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting new users today: {str(e)}")
            return 0

    async def get_pending_moderation_count(self) -> int:
        """Get pending moderation posts count."""
        try:
            reports_col = self.mongo_db["moderation_reports"]
            count = await reports_col.count_documents({"status": "pending"})
            return count
        except Exception as e:
            logger.error(f"Error getting pending moderation count: {str(e)}")
            return 0

    async def get_delivery_queue(
        self, status: str = "pending", page: int = 1, page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get delivery queue with pagination."""
        from app.modules.orders.models import Order
        
        try:
            # Get orders with pending status
            offset = (page - 1) * page_size
            
            query = select(Order).where(
                Order.status == status
            ).order_by(Order.created_at).offset(offset).limit(page_size)
            
            result = await self.db.execute(query)
            orders = result.scalars().all()
            
            # Count total
            count_query = select(func.count(Order.id)).where(Order.status == status)
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0
            
            # Format delivery info
            deliveries = []
            for order in orders:
                from app.modules.users.models import User
                
                user_query = select(User).where(User.id == order.user_id)
                user_result = await self.db.execute(user_query)
                user = user_result.scalar()
                
                deliveries.append({
                    "order_id": str(order.id),
                    "user_id": str(order.user_id),
                    "user_email": user.email if user else "N/A",
                    "delivery_address": order.delivery_address or {},
                    "delivery_lat": order.delivery_address.get("latitude", 0) if order.delivery_address else 0,
                    "delivery_lon": order.delivery_address.get("longitude", 0) if order.delivery_address else 0,
                    "status": order.status,
                    "created_at": order.created_at,
                })
            
            return deliveries, total
        except Exception as e:
            logger.error(f"Error getting delivery queue: {str(e)}")
            return [], 0

    async def update_delivery_status(
        self,
        order_id: str,
        status: str,
        delivery_lat: Optional[float] = None,
        delivery_lon: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update delivery status."""
        from app.modules.orders.models import Order
        from sqlalchemy.orm import Session
        
        try:
            query = select(Order).where(Order.id == order_id)
            result = await self.db.execute(query)
            order = result.scalar()
            
            if not order:
                return False
            
            order.status = status
            if delivery_lat and delivery_lon:
                if not order.delivery_address:
                    order.delivery_address = {}
                order.delivery_address["latitude"] = delivery_lat
                order.delivery_address["longitude"] = delivery_lon
            if notes:
                if not order.delivery_address:
                    order.delivery_address = {}
                order.delivery_address["notes"] = notes
            
            self.db.add(order)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            await self.db.rollback()
            return False

    async def create_discount(self, discount_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create discount."""
        try:
            discounts_col = self.mongo_db["discounts"]
            result = await discounts_col.insert_one(discount_data)
            discount_data["id"] = str(result.inserted_id)
            return discount_data
        except Exception as e:
            logger.error(f"Error creating discount: {str(e)}")
            raise

    async def get_discount(self, code: str) -> Optional[Dict[str, Any]]:
        """Get discount by code."""
        try:
            discounts_col = self.mongo_db["discounts"]
            discount = await discounts_col.find_one({"code": code})
            return discount
        except Exception as e:
            logger.error(f"Error getting discount: {str(e)}")
            return None

    async def get_all_discounts(self) -> List[Dict[str, Any]]:
        """Get all discounts."""
        try:
            discounts_col = self.mongo_db["discounts"]
            discounts = []
            async for discount in discounts_col.find():
                discount["id"] = str(discount.get("_id"))
                discounts.append(discount)
            return discounts
        except Exception as e:
            logger.error(f"Error getting all discounts: {str(e)}")
            return []

    async def update_discount(
        self, code: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update discount."""
        try:
            discounts_col = self.mongo_db["discounts"]
            result = await discounts_col.update_one(
                {"code": code},
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating discount: {str(e)}")
            return False

    async def delete_discount(self, code: str) -> bool:
        """Delete discount."""
        try:
            discounts_col = self.mongo_db["discounts"]
            result = await discounts_col.delete_one({"code": code})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting discount: {str(e)}")
            return False

    async def create_job_posting(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create job posting."""
        try:
            jobs_col = self.mongo_db["jobs"]
            result = await jobs_col.insert_one(job_data)
            job_data["id"] = str(result.inserted_id)
            return job_data
        except Exception as e:
            logger.error(f"Error creating job posting: {str(e)}")
            raise

    async def get_all_jobs(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all job postings."""
        try:
            jobs_col = self.mongo_db["jobs"]
            query = {"is_active": True} if active_only else {}
            
            jobs = []
            async for job in jobs_col.find(query).sort("created_at", -1):
                job["id"] = str(job.get("_id"))
                jobs.append(job)
            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {str(e)}")
            return []

    async def update_job_posting(
        self, job_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update job posting."""
        from bson import ObjectId
        
        try:
            jobs_col = self.mongo_db["jobs"]
            result = await jobs_col.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating job posting: {str(e)}")
            return False

    async def delete_job_posting(self, job_id: str) -> bool:
        """Delete job posting."""
        from bson import ObjectId
        
        try:
            jobs_col = self.mongo_db["jobs"]
            result = await jobs_col.delete_one({"_id": ObjectId(job_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting job posting: {str(e)}")
            return False
