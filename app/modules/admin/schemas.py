"""Admin module schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class DiscountType(str, Enum):
    """Discount type enum."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class CreateDiscountRequest(BaseModel):
    """Create discount request."""
    code: str = Field(..., min_length=3, max_length=20, description="Discount code")
    discount_type: DiscountType = Field(..., description="Type of discount")
    value: float = Field(..., gt=0, description="Discount value (amount or percentage)")
    min_order_amount: float = Field(default=0, ge=0, description="Minimum order amount")
    max_discount_amount: Optional[float] = Field(default=None, gt=0, description="Max discount amount (for percentage)")
    max_uses: Optional[int] = Field(default=None, gt=0, description="Maximum number of uses")
    usage_count: int = Field(default=0, description="Current usage count")
    start_date: datetime = Field(..., description="Discount start date")
    end_date: datetime = Field(..., description="Discount end date")
    is_active: bool = Field(default=True, description="Is discount active")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "SUMMER20",
                "discount_type": "percentage",
                "value": 20,
                "min_order_amount": 1000,
                "max_discount_amount": 500,
                "max_uses": 100,
                "start_date": "2024-06-01T00:00:00Z",
                "end_date": "2024-08-31T23:59:59Z",
                "is_active": True,
            }
        }


class UpdateDiscountRequest(BaseModel):
    """Update discount request."""
    is_active: Optional[bool] = Field(default=None, description="Is discount active")
    max_uses: Optional[int] = Field(default=None, gt=0, description="Maximum number of uses")
    end_date: Optional[datetime] = Field(default=None, description="Discount end date")


class DiscountResponse(BaseModel):
    """Discount response."""
    id: str = Field(..., description="Discount ID")
    code: str = Field(..., description="Discount code")
    discount_type: DiscountType = Field(..., description="Type of discount")
    value: float = Field(..., description="Discount value")
    min_order_amount: float = Field(..., description="Minimum order amount")
    max_discount_amount: Optional[float] = Field(..., description="Max discount amount")
    max_uses: Optional[int] = Field(..., description="Maximum number of uses")
    usage_count: int = Field(..., description="Current usage count")
    start_date: datetime = Field(..., description="Discount start date")
    end_date: datetime = Field(..., description="Discount end date")
    is_active: bool = Field(..., description="Is discount active")
    created_at: datetime = Field(..., description="Created at")


class JobPostingType(str, Enum):
    """Job posting type."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"


class CreateJobPostingRequest(BaseModel):
    """Create job posting request."""
    title: str = Field(..., min_length=5, max_length=100, description="Job title")
    description: str = Field(..., min_length=20, description="Job description")
    job_type: JobPostingType = Field(..., description="Type of job")
    salary_min: float = Field(..., gt=0, description="Minimum salary")
    salary_max: float = Field(..., gt=0, description="Maximum salary")
    location: str = Field(..., min_length=3, description="Job location")
    required_skills: List[str] = Field(..., min_items=1, description="Required skills")
    experience_level: str = Field(..., description="Experience level (entry/mid/senior)")
    is_active: bool = Field(default=True, description="Is job posting active")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Guitar Technician",
                "description": "We are looking for an experienced guitar technician...",
                "job_type": "full_time",
                "salary_min": 25000,
                "salary_max": 40000,
                "location": "Delhi",
                "required_skills": ["guitar repair", "electronics", "customer service"],
                "experience_level": "mid",
                "is_active": True,
            }
        }


class JobPostingResponse(BaseModel):
    """Job posting response."""
    id: str = Field(..., description="Job posting ID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    job_type: JobPostingType = Field(..., description="Type of job")
    salary_min: float = Field(..., description="Minimum salary")
    salary_max: float = Field(..., description="Maximum salary")
    location: str = Field(..., description="Job location")
    required_skills: List[str] = Field(..., description="Required skills")
    experience_level: str = Field(..., description="Experience level")
    is_active: bool = Field(..., description="Is job posting active")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class RevenueMetrics(BaseModel):
    """Revenue metrics."""
    total_revenue: float = Field(..., description="Total revenue")
    total_orders: int = Field(..., description="Total number of orders")
    total_transactions: int = Field(..., description="Total transactions")
    average_order_value: float = Field(..., description="Average order value")
    successful_orders: int = Field(..., description="Successfully completed orders")
    pending_orders: int = Field(..., description="Pending orders")
    cancelled_orders: int = Field(..., description="Cancelled orders")


class PopularProduct(BaseModel):
    """Popular product info."""
    product_id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sale_count: int = Field(..., description="Number of sales")
    revenue: float = Field(..., description="Revenue from product")
    rating: float = Field(..., description="Product rating")


class TopSellingProducts(BaseModel):
    """Top selling products."""
    products: List[PopularProduct] = Field(..., description="List of top products")
    total_products: int = Field(..., description="Total products sold")


class DashboardResponse(BaseModel):
    """Admin dashboard response."""
    revenue_metrics: RevenueMetrics = Field(..., description="Revenue metrics")
    top_selling_products: TopSellingProducts = Field(..., description="Top selling products")
    pending_deliveries: int = Field(..., description="Pending deliveries")
    total_users: int = Field(..., description="Total users")
    new_users_today: int = Field(..., description="New users today")
    pending_moderation_posts: int = Field(..., description="Posts pending moderation")


class DeliveryStatus(str, Enum):
    """Delivery status."""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class UpdateDeliveryRequest(BaseModel):
    """Update delivery status request."""
    status: DeliveryStatus = Field(..., description="Delivery status")
    delivery_lat: Optional[float] = Field(default=None, description="Delivery latitude")
    delivery_lon: Optional[float] = Field(default=None, description="Delivery longitude")
    notes: Optional[str] = Field(default=None, max_length=500, description="Delivery notes")


class DeliveryInfo(BaseModel):
    """Delivery information."""
    order_id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    user_email: str = Field(..., description="User email")
    delivery_address: dict = Field(..., description="Delivery address")
    delivery_lat: float = Field(..., description="Delivery latitude")
    delivery_lon: float = Field(..., description="Delivery longitude")
    status: str = Field(..., description="Delivery status")
    created_at: datetime = Field(..., description="Order created at")


class DeliveryQueueResponse(BaseModel):
    """Delivery queue response."""
    deliveries: List[DeliveryInfo] = Field(..., description="List of pending deliveries")
    total_count: int = Field(..., description="Total pending deliveries")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class AdminStatsResponse(BaseModel):
    """Admin statistics response."""
    total_revenue: float = Field(..., description="Total revenue")
    total_orders: int = Field(..., description="Total orders")
    total_users: int = Field(..., description="Total users")
    total_products: int = Field(..., description="Total products")
    active_discounts: int = Field(..., description="Active discounts")
    pending_moderation: int = Field(..., description="Posts pending moderation")
    pending_deliveries: int = Field(..., description="Pending deliveries")
    average_rating: float = Field(..., description="Average product rating")


class ShopSettingsRequest(BaseModel):
    """Shop settings update request."""
    shop_address: str = Field(..., min_length=5, description="Physical address of the shop")
    shop_lat: float = Field(..., description="Latitude of the shop")
    shop_lon: float = Field(..., description="Longitude of the shop")
    delivery_radius_km: float = Field(..., gt=0, description="Delivery radius in kilometers")


class ShopSettingsResponse(BaseModel):
    """Shop settings response."""
    shop_address: str = Field(..., description="Physical address of the shop")
    shop_lat: float = Field(..., description="Latitude of the shop")
    shop_lon: float = Field(..., description="Longitude of the shop")
    delivery_radius_km: float = Field(..., description="Delivery radius in kilometers")
    updated_at: datetime = Field(..., description="Last updated at")
