"""Admin module router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.core import get_db, get_mongo_db, get_settings
from app.core.security import verify_token, get_current_user
from app.modules.admin.schemas import (
    DashboardResponse,
    AdminStatsResponse,
    CreateDiscountRequest,
    UpdateDiscountRequest,
    DiscountResponse,
    CreateJobPostingRequest,
    JobPostingResponse,
    DeliveryQueueResponse,
    UpdateDeliveryRequest,
    DeliveryInfo,
)
from app.modules.admin.service import AdminService
from app.modules.admin.repository import AdminRepository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def admin_service(
    db: AsyncSession = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> AdminService:
    """Get admin service."""
    repository = AdminRepository(db, mongo_db)
    return AdminService(repository)


async def verify_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Verify current user is admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Only admins can access this resource",
        )
    return current_user


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Get admin dashboard with key metrics.
    
    Returns:
    - Revenue metrics (total revenue, orders, average order value)
    - Top selling products with sales count and revenue
    - Pending deliveries count
    - Total and new users
    - Posts pending moderation
    
    Requires: Admin role
    """
    try:
        dashboard = await service.get_dashboard()
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard")


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Get comprehensive admin statistics.
    
    Returns:
    - Total revenue and orders
    - Total users and products
    - Active discounts count
    - Pending moderation posts
    - Pending deliveries
    - Average product rating
    
    Requires: Admin role
    """
    try:
        stats = await service.get_admin_stats()
        return AdminStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# Discount management endpoints

@router.post("/discounts", response_model=DiscountResponse)
async def create_discount(
    request: CreateDiscountRequest,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Create new discount.
    
    Parameters:
    - code: Unique discount code
    - discount_type: 'fixed' or 'percentage'
    - value: Discount amount or percentage
    - min_order_amount: Minimum order to apply discount
    - max_discount_amount: Maximum discount (for percentage discounts)
    - max_uses: Maximum number of uses
    - start_date & end_date: Validity period
    
    Requires: Admin role
    """
    try:
        # Check if code already exists
        existing = await service.get_discount(request.code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Discount code already exists",
            )
        
        discount_data = request.model_dump()
        discount = await service.create_discount(discount_data)
        return DiscountResponse(**discount)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating discount: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create discount")


@router.get("/discounts", response_model=List[DiscountResponse])
async def get_discounts(
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Get all discounts.
    
    Requires: Admin role
    """
    try:
        discounts = await service.get_all_discounts()
        return [DiscountResponse(**d) for d in discounts]
    except Exception as e:
        logger.error(f"Error getting discounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get discounts")


@router.put("/discounts/{code}", response_model=DiscountResponse)
async def update_discount(
    code: str,
    request: UpdateDiscountRequest,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Update discount.
    
    Parameters:
    - is_active: Activate/deactivate discount
    - max_uses: Update maximum uses
    - end_date: Update expiry date
    
    Requires: Admin role
    """
    try:
        discount = await service.get_discount(code)
        if not discount:
            raise HTTPException(
                status_code=404,
                detail="Discount not found",
            )
        
        update_data = request.model_dump(exclude_unset=True)
        success = await service.update_discount(code, update_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update discount")
        
        updated_discount = await service.get_discount(code)
        return DiscountResponse(**updated_discount)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discount: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update discount")


@router.delete("/discounts/{code}")
async def delete_discount(
    code: str,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Delete discount.
    
    Requires: Admin role
    """
    try:
        discount = await service.get_discount(code)
        if not discount:
            raise HTTPException(
                status_code=404,
                detail="Discount not found",
            )
        
        success = await service.delete_discount(code)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete discount")
        
        return {"message": f"Discount {code} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting discount: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete discount")


# Job posting management endpoints

@router.post("/jobs", response_model=JobPostingResponse)
async def create_job(
    request: CreateJobPostingRequest,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Create new job posting.
    
    Parameters:
    - title: Job title
    - description: Job description
    - job_type: 'full_time', 'part_time', or 'freelance'
    - salary_min & salary_max: Salary range
    - location: Job location
    - required_skills: List of required skills
    - experience_level: 'entry', 'mid', or 'senior'
    
    Requires: Admin role
    """
    try:
        job_data = request.model_dump()
        job = await service.create_job_posting(job_data)
        return JobPostingResponse(**job)
    except Exception as e:
        logger.error(f"Error creating job posting: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job posting")


@router.get("/jobs", response_model=List[JobPostingResponse])
async def get_jobs(
    active_only: bool = Query(True),
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Get all job postings.
    
    Parameters:
    - active_only: Filter for active jobs only (default: true)
    
    Requires: Admin role
    """
    try:
        jobs = await service.get_all_jobs(active_only)
        return [JobPostingResponse(**j) for j in jobs]
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get jobs")


@router.put("/jobs/{job_id}", response_model=JobPostingResponse)
async def update_job(
    job_id: str,
    request: CreateJobPostingRequest,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Update job posting.
    
    Parameters:
    - job_id: Job posting ID
    - Updated job details (same as create)
    
    Requires: Admin role
    """
    try:
        update_data = request.model_dump()
        success = await service.update_job_posting(job_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job posting not found",
            )
        
        # Fetch updated job
        jobs = await service.get_all_jobs(active_only=False)
        updated_job = next((j for j in jobs if str(j.get("id")) == job_id), None)
        if not updated_job:
            raise HTTPException(status_code=404, detail="Job posting not found")
        
        return JobPostingResponse(**updated_job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update job posting")


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Delete job posting.
    
    Requires: Admin role
    """
    try:
        success = await service.delete_job_posting(job_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job posting not found",
            )
        
        return {"message": f"Job posting {job_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete job posting")


# Delivery management endpoints

@router.get("/deliveries", response_model=DeliveryQueueResponse)
async def get_deliveries(
    status: str = Query("pending", description="Delivery status filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Get delivery queue with pagination.
    
    Parameters:
    - status: Filter by status ('pending', 'in_transit', 'delivered', 'cancelled')
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    
    Requires: Admin role
    """
    try:
        deliveries, total = await service.get_delivery_queue(
            status, page, page_size
        )
        return DeliveryQueueResponse(
            deliveries=[DeliveryInfo(**d) for d in deliveries],
            total_count=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Error getting deliveries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get deliveries")


@router.put("/deliveries/{order_id}")
async def update_delivery(
    order_id: str,
    request: UpdateDeliveryRequest,
    _: dict = Depends(verify_admin_user),
    service: AdminService = Depends(admin_service),
):
    """Update delivery status.
    
    Parameters:
    - order_id: Order ID
    - status: New delivery status
    - delivery_lat & delivery_lon: Delivery location coordinates
    - notes: Delivery notes
    
    Requires: Admin role
    """
    try:
        success = await service.update_delivery_status(
            order_id,
            request.status,
            request.delivery_lat,
            request.delivery_lon,
            request.notes,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )
        
        return {
            "message": f"Delivery for order {order_id} updated to {request.status}",
            "status": request.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating delivery: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update delivery")
