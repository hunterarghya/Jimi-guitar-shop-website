"""Admin module service."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    DashboardResponse,
    RevenueMetrics,
    TopSellingProducts,
    PopularProduct,
    DeliveryStatus,
)
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """Admin service for business logic."""

    def __init__(self, repository: AdminRepository):
        """Initialize service."""
        self.repository = repository

    async def get_dashboard(self) -> DashboardResponse:
        """Get admin dashboard data."""
        try:
            # Get revenue metrics
            revenue_data = await self.repository.get_revenue_metrics()
            revenue_metrics = RevenueMetrics(**revenue_data)
            
            # Get top selling products
            products_data = await self.repository.get_top_selling_products(limit=10)
            top_selling_products = TopSellingProducts(
                products=[PopularProduct(**p) for p in products_data],
                total_products=sum(p["sale_count"] for p in products_data),
            )
            
            # Get other metrics
            pending_deliveries = await self.repository.get_pending_deliveries_count()
            total_users = await self.repository.get_total_users()
            new_users_today = await self.repository.get_new_users_today()
            pending_moderation_posts = await self.repository.get_pending_moderation_count()
            
            return DashboardResponse(
                revenue_metrics=revenue_metrics,
                top_selling_products=top_selling_products,
                pending_deliveries=pending_deliveries,
                total_users=total_users,
                new_users_today=new_users_today,
                pending_moderation_posts=pending_moderation_posts,
            )
        except Exception as e:
            logger.error(f"Error getting dashboard: {str(e)}")
            raise

    async def create_discount(
        self, discount_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create discount."""
        try:
            discount_data["created_at"] = datetime.utcnow()
            return await self.repository.create_discount(discount_data)
        except Exception as e:
            logger.error(f"Error creating discount: {str(e)}")
            raise

    async def get_discount(self, code: str) -> Optional[Dict[str, Any]]:
        """Get discount by code."""
        try:
            return await self.repository.get_discount(code)
        except Exception as e:
            logger.error(f"Error getting discount: {str(e)}")
            return None

    async def get_all_discounts(self) -> List[Dict[str, Any]]:
        """Get all discounts."""
        try:
            return await self.repository.get_all_discounts()
        except Exception as e:
            logger.error(f"Error getting all discounts: {str(e)}")
            return []

    async def update_discount(
        self, code: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update discount."""
        try:
            return await self.repository.update_discount(code, update_data)
        except Exception as e:
            logger.error(f"Error updating discount: {str(e)}")
            return False

    async def delete_discount(self, code: str) -> bool:
        """Delete discount."""
        try:
            return await self.repository.delete_discount(code)
        except Exception as e:
            logger.error(f"Error deleting discount: {str(e)}")
            return False

    async def create_job_posting(
        self, job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create job posting."""
        try:
            job_data["created_at"] = datetime.utcnow()
            job_data["updated_at"] = datetime.utcnow()
            return await self.repository.create_job_posting(job_data)
        except Exception as e:
            logger.error(f"Error creating job posting: {str(e)}")
            raise

    async def get_all_jobs(
        self, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all job postings."""
        try:
            return await self.repository.get_all_jobs(active_only)
        except Exception as e:
            logger.error(f"Error getting jobs: {str(e)}")
            return []

    async def update_job_posting(
        self, job_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update job posting."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            return await self.repository.update_job_posting(job_id, update_data)
        except Exception as e:
            logger.error(f"Error updating job posting: {str(e)}")
            return False

    async def delete_job_posting(self, job_id: str) -> bool:
        """Delete job posting."""
        try:
            return await self.repository.delete_job_posting(job_id)
        except Exception as e:
            logger.error(f"Error deleting job posting: {str(e)}")
            return False

    async def get_delivery_queue(
        self, status: str = "pending", page: int = 1, page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get delivery queue."""
        try:
            return await self.repository.get_delivery_queue(status, page, page_size)
        except Exception as e:
            logger.error(f"Error getting delivery queue: {str(e)}")
            return [], 0

    async def update_delivery_status(
        self,
        order_id: str,
        status: DeliveryStatus,
        delivery_lat: Optional[float] = None,
        delivery_lon: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update delivery status."""
        try:
            return await self.repository.update_delivery_status(
                order_id, status.value, delivery_lat, delivery_lon, notes
            )
        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            return False

    async def get_admin_stats(self) -> Dict[str, Any]:
        """Get comprehensive admin statistics."""
        try:
            revenue_data = await self.repository.get_revenue_metrics()
            total_users = await self.repository.get_total_users()
            pending_moderation = await self.repository.get_pending_moderation_count()
            pending_deliveries = await self.repository.get_pending_deliveries_count()
            
            # Get total products count from MongoDB
            products_col = self.repository.mongo_db["products"]
            total_products = await products_col.count_documents({})
            
            # Get active discounts count
            discounts_col = self.repository.mongo_db["discounts"]
            active_discounts = await discounts_col.count_documents({
                "is_active": True,
                "end_date": {"$gt": datetime.utcnow()},
            })
            
            # Get average rating
            pipeline = [
                {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}},
            ]
            result = []
            async for doc in products_col.aggregate(pipeline):
                result.append(doc)
            
            average_rating = result[0]["avg_rating"] if result else 0
            
            return {
                "total_revenue": revenue_data["total_revenue"],
                "total_orders": revenue_data["total_orders"],
                "total_users": total_users,
                "total_products": total_products,
                "active_discounts": active_discounts,
                "pending_moderation": pending_moderation,
                "pending_deliveries": pending_deliveries,
                "average_rating": round(average_rating, 2),
            }
        except Exception as e:
            logger.error(f"Error getting admin stats: {str(e)}")
            raise
