# Jimi - Guitar & Musical Instrument Shop API Documentation

## Overview

Jimi is a **production-grade platform** combining:

- **E-commerce**: Full shopping experience with products, cart, orders, and payments
- **Social Media**: Posts, comments, likes, saves for musicians to share and connect
- **Admin Dashboard**: Revenue analytics, order management, delivery tracking, discounts, job postings
- **Chatbot**: Rule-based AI assistant with FAQ integration and intent detection

**Tech Stack**: Python 3.12, FastAPI, PostgreSQL, MongoDB, Redis, Razorpay, Docker Compose

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)
- Environment variables configured (see `.env.example`)

### Running the Platform

```bash
# Clone the repository
git clone <repo-url>
cd jimi

# Copy environment variables
cp .env.example .env

# Start all services with Docker Compose
docker-compose up -d

# Verify all services are healthy
curl http://localhost:8000/health
```

**Services will be available at:**

- **API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc` (Alternative docs)
- **PostgreSQL**: `localhost:5432`
- **MongoDB**: `localhost:27017`
- **Redis**: `localhost:6379`
- **NGINX**: `http://localhost` (production proxy)

---

## Authentication

### JWT Token Flow

All protected endpoints require JWT bearer token in `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Registration

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "9876543210",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}

Response (201):
{
  "user_id": "uuid",
  "email": "user@example.com",
  "message": "User registered. Verify your email to activate."
}
```

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response (200):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_verified": true,
    "is_admin": false
  }
}
```

### Refresh Token

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200):
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token"
}
```

### OTP Login (Optional)

```bash
POST /api/v1/auth/otp/request
{
  "contact": "user@example.com"  # or phone
}

POST /api/v1/auth/otp/verify
{
  "contact": "user@example.com",
  "otp": "123456"
}
```

---

## Products API

### List Products

```bash
GET /api/v1/products?page=1&page_size=20&category=acoustic&min_price=1000&max_price=50000&sort_by=rating&sort_order=desc
```

**Query Parameters:**

- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `category` (str): Filter by category
- `min_price` (float): Minimum price
- `max_price` (float): Maximum price
- `brand` (str): Filter by brand
- `rating_min` (float): Minimum rating (0-5)
- `sort_by` (str): `price`, `rating`, `created_at` (default: `rating`)
- `sort_order` (str): `asc` or `desc`

**Response (200):**

```json
{
  "data": [
    {
      "id": "product-123",
      "name": "Yamaha Acoustic Guitar",
      "description": "Professional acoustic guitar",
      "category": "acoustic",
      "price": 25000,
      "stock": 15,
      "rating": 4.5,
      "images": ["url1", "url2"],
      "brand": "Yamaha"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150
  }
}
```

### Search Products

```bash
GET /api/v1/products/search?q=acoustic+yamaha&page=1
```

Uses MongoDB full-text search on product name, description, brand, category.

### Get Product Details

```bash
GET /api/v1/products/{product_id}
```

### Create Product (Admin Only)

```bash
POST /api/v1/products
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "name": "Fender Stratocaster",
  "description": "Classic electric guitar",
  "category": "electric",
  "price": 75000,
  "stock": 10,
  "brand": "Fender",
  "specifications": {
    "type": "electric",
    "body_wood": "alder",
    "strings": 6
  }
}
```

### Update Product (Admin Only)

```bash
PUT /api/v1/products/{product_id}
Authorization: Bearer <admin-token>
```

### Delete Product (Admin Only)

```bash
DELETE /api/v1/products/{product_id}
Authorization: Bearer <admin-token>
```

---

## Cart API

### Get Cart

```bash
GET /api/v1/cart
Authorization: Bearer <token>

Response (200):
{
  "items": [
    {
      "product_id": "prod-123",
      "quantity": 2,
      "price": 25000,
      "subtotal": 50000
    }
  ],
  "total_amount": 50000,
  "item_count": 1
}
```

### Add to Cart

```bash
POST /api/v1/cart/items
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": "prod-123",
  "quantity": 2
}

Response (201):
{
  "message": "Item added to cart",
  "item_count": 2
}
```

**Constraints:**

- Max 10 units per product
- Max 10 different products in cart

### Update Cart Item

```bash
PUT /api/v1/cart/items/{product_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "quantity": 3
}
```

### Remove from Cart

```bash
DELETE /api/v1/cart/items/{product_id}
Authorization: Bearer <token>
```

### Clear Cart

```bash
DELETE /api/v1/cart
Authorization: Bearer <token>
```

---

## Orders & Payments API

### Create Order

```bash
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "delivery_address": {
    "street": "123 Main St",
    "city": "Delhi",
    "state": "Delhi",
    "postal_code": "110001",
    "country": "India",
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "apply_discount_code": "SUMMER20"
}

Response (201):
{
  "order_id": "order-123",
  "total_amount": 45000,
  "razorpay_order_id": "rzp_order_123",
  "payment_url": "https://rzp.io/i/...",
  "items": [...]
}
```

**Notes:**

- Cart is cleared after order creation
- Inventory is locked pessimistically during checkout
- Distance-based delivery validation (default: 10km radius)

### Get Orders

```bash
GET /api/v1/orders?page=1&status=pending
Authorization: Bearer <token>

Query Parameters:
- page (int): Page number
- status (str): pending, confirmed, completed, cancelled
```

### Get Order Details

```bash
GET /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

### Verify Payment

```bash
POST /api/v1/orders/{order_id}/verify-payment
Authorization: Bearer <token>
Content-Type: application/json

{
  "razorpay_payment_id": "pay_123",
  "razorpay_signature": "signature_hex"
}

Response (200):
{
  "order_id": "order-123",
  "status": "confirmed",
  "payment_status": "completed"
}
```

**Payment Verification:**

- HMAC-SHA256 signature validation
- Razorpay webhook support at `/api/v1/orders/razorpay-webhook`

### Get Payments

```bash
GET /api/v1/orders/payments
Authorization: Bearer <token>
```

---

## Social Media API

### Get Posts Feed

```bash
GET /api/v1/social/posts?page=1&page_size=20
Authorization: Bearer <token>

Response (200):
{
  "data": [
    {
      "id": "post-123",
      "user_id": "user-456",
      "user_name": "John Guitarist",
      "user_avatar": "url",
      "content": "Just bought my first Fender!",
      "images": ["url1", "url2"],
      "likes_count": 42,
      "comments_count": 5,
      "saves_count": 3,
      "is_liked_by_user": true,
      "is_saved_by_user": true,
      "status": "published",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 350
  }
}
```

### Create Post

```bash
POST /api/v1/social/posts
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Check out my new guitar setup!",
  "images": [
    {
      "url": "https://...",
      "caption": "My new Yamaha"
    }
  ],
  "hashtags": ["guitar", "setup", "music"]
}

Response (201):
{
  "id": "post-123",
  "status": "pending",
  "message": "Post created. Awaiting moderation."
}
```

### Update Post

```bash
PUT /api/v1/social/posts/{post_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Updated content"
}
```

### Delete Post

```bash
DELETE /api/v1/social/posts/{post_id}
Authorization: Bearer <token>
```

### Like Post

```bash
POST /api/v1/social/posts/{post_id}/like
Authorization: Bearer <token>

Response (200):
{
  "post_id": "post-123",
  "likes_count": 43
}
```

### Unlike Post

```bash
DELETE /api/v1/social/posts/{post_id}/like
Authorization: Bearer <token>
```

### Save Post

```bash
POST /api/v1/social/posts/{post_id}/save
Authorization: Bearer <token>
```

### Unsave Post

```bash
DELETE /api/v1/social/posts/{post_id}/save
Authorization: Bearer <token>
```

### Get Saved Posts

```bash
GET /api/v1/social/saved
Authorization: Bearer <token>
```

### Add Comment

```bash
POST /api/v1/social/posts/{post_id}/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "Great guitar!"
}
```

### Get Comments

```bash
GET /api/v1/social/posts/{post_id}/comments?page=1
```

### Delete Comment

```bash
DELETE /api/v1/social/comments/{comment_id}
Authorization: Bearer <token>
```

---

## Content Moderation API

### Report Post

```bash
POST /api/v1/moderation/posts/{post_id}/report
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "inappropriate",  # spam, inappropriate, hate_speech, misinformation, harassment, other
  "description": "This post contains offensive content"
}

Response (201):
{
  "report_id": "report-123",
  "status": "pending"
}
```

### Get Moderation Queue (Admin)

```bash
GET /api/v1/moderation/pending?page=1&page_size=20
Authorization: Bearer <admin-token>

Response (200):
{
  "pending_posts": [
    {
      "post_id": "post-123",
      "user_id": "user-456",
      "content": "...",
      "report_count": 3,
      "report_reasons": ["spam", "inappropriate"],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25
}
```

### Approve Post (Admin)

```bash
PUT /api/v1/moderation/posts/{post_id}/approve
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "reason": "Content is appropriate"
}
```

### Reject Post (Admin)

```bash
PUT /api/v1/moderation/posts/{post_id}/reject
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "reason": "Violates community guidelines"
}
```

### Delete Post (Admin)

```bash
DELETE /api/v1/moderation/posts/{post_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "reason": "Hate speech violation"
}
```

### Get Moderation Statistics (Admin)

```bash
GET /api/v1/moderation/statistics
Authorization: Bearer <admin-token>
```

---

## Admin Dashboard API

### Get Dashboard

```bash
GET /api/v1/admin/dashboard
Authorization: Bearer <admin-token>

Response (200):
{
  "revenue_metrics": {
    "total_revenue": 500000,
    "total_orders": 125,
    "average_order_value": 4000,
    "successful_orders": 120,
    "pending_orders": 5,
    "cancelled_orders": 0
  },
  "top_selling_products": {
    "products": [
      {
        "product_id": "prod-123",
        "name": "Yamaha Acoustic",
        "sale_count": 45,
        "revenue": 1125000,
        "rating": 4.8
      }
    ],
    "total_products": 425
  },
  "pending_deliveries": 12,
  "total_users": 3450,
  "new_users_today": 15,
  "pending_moderation_posts": 8
}
```

### Get Statistics

```bash
GET /api/v1/admin/stats
Authorization: Bearer <admin-token>
```

---

## Discount Management (Admin)

### Create Discount

```bash
POST /api/v1/admin/discounts
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "code": "SUMMER20",
  "discount_type": "percentage",  # fixed or percentage
  "value": 20,  # percentage or amount
  "min_order_amount": 1000,
  "max_discount_amount": 500,  # for percentage discounts
  "max_uses": 100,
  "start_date": "2024-06-01T00:00:00Z",
  "end_date": "2024-08-31T23:59:59Z",
  "is_active": true
}
```

### List Discounts

```bash
GET /api/v1/admin/discounts
Authorization: Bearer <admin-token>
```

### Update Discount

```bash
PUT /api/v1/admin/discounts/{code}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "is_active": false,
  "end_date": "2024-07-31T23:59:59Z"
}
```

### Delete Discount

```bash
DELETE /api/v1/admin/discounts/{code}
Authorization: Bearer <admin-token>
```

---

## Job Postings (Admin)

### Create Job Posting

```bash
POST /api/v1/admin/jobs
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "title": "Guitar Technician",
  "description": "We are looking for an experienced guitar technician...",
  "job_type": "full_time",  # full_time, part_time, freelance
  "salary_min": 25000,
  "salary_max": 40000,
  "location": "Delhi",
  "required_skills": ["guitar repair", "electronics", "customer service"],
  "experience_level": "mid",  # entry, mid, senior
  "is_active": true
}
```

### List Jobs

```bash
GET /api/v1/admin/jobs?active_only=true
Authorization: Bearer <admin-token>
```

### Update Job

```bash
PUT /api/v1/admin/jobs/{job_id}
Authorization: Bearer <admin-token>
```

### Delete Job

```bash
DELETE /api/v1/admin/jobs/{job_id}
Authorization: Bearer <admin-token>
```

---

## Delivery Management (Admin)

### Get Delivery Queue

```bash
GET /api/v1/admin/deliveries?status=pending&page=1&page_size=20
Authorization: Bearer <admin-token>

Query Parameters:
- status (str): pending, in_transit, delivered, cancelled
- page (int): Page number
- page_size (int): Items per page
```

### Update Delivery Status

```bash
PUT /api/v1/admin/deliveries/{order_id}
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "status": "in_transit",
  "delivery_lat": 28.6139,
  "delivery_lon": 77.2090,
  "notes": "Package picked up from warehouse"
}
```

---

## Chatbot API

### Start Conversation

```bash
POST /api/v1/chatbot/start
Authorization: Bearer <token>

Response (200):
{
  "conversation_id": "conv_abc123",
  "initial_message": {
    "type": "text",
    "text": "Hello! Welcome to Jimi Music. How can I help you today?",
    "buttons": [
      {"label": "Guitar Selection", "value": "guitar_selection"},
      {"label": "Browse Products", "value": "products"},
      {"label": "FAQs", "value": "faqs"}
    ]
  }
}
```

### Chat Message

```bash
POST /api/v1/chatbot/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "I'm a beginner guitarist, what should I buy?",
  "conversation_id": "conv_abc123"
}

Response (200):
{
  "conversation_id": "conv_abc123",
  "user_message": "I'm a beginner guitarist, what should I buy?",
  "bot_response": {
    "type": "text",
    "text": "Great! I can help you choose the right guitar...",
    "buttons": [...]
  },
  "confidence": 0.95,
  "intent": "guitar_selection",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Conversation History

```bash
GET /api/v1/chatbot/conversations/{conversation_id}/history
Authorization: Bearer <token>
```

### Get My Conversations

```bash
GET /api/v1/chatbot/my-conversations
Authorization: Bearer <token>
```

### Get FAQs

```bash
GET /api/v1/chatbot/faqs?category=beginner_guide

Response (200):
[
  {
    "question": "What's the difference between acoustic and electric guitars?",
    "answer": "Acoustic guitars produce sound naturally...",
    "category": "beginner_guide",
    "keywords": ["acoustic", "electric"]
  }
]
```

### Search FAQs

```bash
GET /api/v1/chatbot/faqs/search?query=guitar+size
```

### Create FAQ (Admin)

```bash
POST /api/v1/chatbot/faqs
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "question": "How do I maintain my guitar?",
  "answer": "Regular maintenance is essential...",
  "category": "maintenance",
  "keywords": ["maintenance", "care", "cleaning"]
}
```

---

## Error Handling

All endpoints return standard error format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Common HTTP Status Codes:**

- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `409`: Conflict (duplicate resource)
- `422`: Unprocessable Entity (invalid data)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

---

## Rate Limiting

- **Default**: 100 requests per 60 seconds
- **Login**: 5 attempts per 300 seconds
- **Returns**: `429 Too Many Requests` when exceeded

---

## Data Models

### User

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "phone": "9876543210",
  "full_name": "John Doe",
  "is_verified": true,
  "is_admin": false,
  "avatar_url": "https://...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Product

```json
{
  "id": "uuid",
  "name": "Yamaha Acoustic Guitar",
  "category": "acoustic",
  "brand": "Yamaha",
  "price": 25000,
  "stock": 15,
  "rating": 4.5,
  "description": "Professional grade...",
  "specifications": {},
  "images": ["url1", "url2"]
}
```

### Order

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "items": [
    {
      "product_id": "uuid",
      "name": "Product",
      "price": 25000,
      "quantity": 2
    }
  ],
  "total_amount": 50000,
  "delivery_address": {},
  "status": "pending",  # pending, confirmed, completed, cancelled
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Post

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "content": "Post content",
  "images": [],
  "likes_count": 42,
  "comments_count": 5,
  "status": "published",  # pending, published, rejected
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Webhooks

### Razorpay Payment Webhook

**Endpoint**: `POST /api/v1/orders/razorpay-webhook`

Handles webhook events:

- `payment.authorized`
- `payment.captured`
- `payment.failed`

Verify webhook signature using HMAC-SHA256.

---

## Environment Variables

See `.env.example` for complete configuration:

```bash
# Application
APP_NAME=Jimi - Guitar Shop Platform
APP_VERSION=1.0.0
DEBUG=true

# Databases
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
MONGO_HOST=mongo
MONGO_PORT=27017
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Payments
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Shop
SHOP_RADIUS_KM=10.0
SHOP_LATITUDE=28.6139
SHOP_LONGITUDE=77.2090
```

---

## Performance Considerations

- **Pagination**: All list endpoints support pagination with default 20 items per page
- **Caching**: Redis caches sessions, tokens, and OTPs
- **Indexing**: MongoDB and PostgreSQL have optimized indexes on frequently queried fields
- **Async**: All database operations are async-ready
- **Connection Pooling**: Database connections are pooled for performance

---

## Security Best Practices

1. **Never commit `.env`** - Always use `.env.example` template
2. **HTTPS in Production** - API requires HTTPS in production
3. **JWT Tokens** - Access tokens expire in 30 minutes
4. **Password Hashing** - Argon2 with random salt
5. **CORS** - Configured for approved origins only
6. **HMAC Verification** - Razorpay payments verified with signature
7. **Rate Limiting** - Login attempts rate-limited
8. **Token Revocation** - JTI blocklist in Redis for logout

---

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Production Deployment

1. **Update environment variables** in `.env`
2. **Set DEBUG=false** in production
3. **Use strong SECRET_KEY** (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
4. **Enable HTTPS** in NGINX configuration
5. **Configure database backups** for PostgreSQL and MongoDB
6. **Enable Redis persistence** for data durability
7. **Monitor logs** and set up alerting

---

## Support

For issues, feature requests, or questions:

- **Email**: support@jimi.local
- **Documentation**: http://localhost:8000/docs
- **Issues**: GitHub Issues

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: January 2024  
**API Version**: 1.0.0  
**Status**: Production Ready ✅
