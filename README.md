# Jimi - Guitar & Musical Instrument Shop Platform

Web platform combining e-commerce, social media, admin dashboard, and secure payments.

## Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)

## Quick Start

### 1. Clone & Setup Environment

```bash
cd jimi
cp .env.example .env
# Edit .env with your values
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Access Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:8000 (separate login)
- **NGINX Proxy**: http://localhost:80

### 4. Verify Services

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f app
```

## Local Development (Without Docker)

### Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Application

```bash
uvicorn app.api:app --reload
```

### Run Tests

```bash
pytest tests/ -v --cov=app
```

## Architecture

### Project Structure

```
jimi/
├── app/
│   ├── core/                 # Config, DB, Security
│   ├── modules/              # Feature modules (auth, products, etc.)
│   ├── middleware/           # Error handling, middleware
│   └── api.py               # FastAPI app factory
├── migrations/               # Alembic schema migrations
├── tests/                   # Unit & integration tests
├── docker/                  # Docker & NGINX configs
├── docker-compose.yml       # Service orchestration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md
```

### Modules

- **auth**: JWT, OAuth, OTP, email/phone verification
- **users**: User profiles, RBAC
- **products**: MongoDB catalog, filtering, search
- **cart**: Shopping cart management
- **orders**: Order processing, inventory management
- **payments**: Razorpay integration, webhooks
- **social**: Posts, comments, likes, saves
- **moderation**: Post approval, reporting
- **admin**: Dashboard, analytics, CRUD
- **notifications**: Email, SMS via Celery
- **jobs**: Job postings
- **discounts**: Discount codes & offers
- **chatbot**: Rule-based FAQ helper (extensible for LLMs)

### Tech Stack

**Backend**: FastAPI, SQLAlchemy 2.0, Pydantic v2

**Databases**:

- PostgreSQL: Users, orders, payments, jobs
- MongoDB: Products, posts, comments
- Redis: Sessions, JTI blocklist, rate limits, OTPs

**Services**: Celery + Redis, ImageKit, Razorpay

**Infra**: Docker, Docker Compose, NGINX

## API Endpoints (v1)

All endpoints prefixed with `/api/v1`

### Auth

- `POST /auth/register` - User registration
- `POST /auth/login` - Email/password login
- `POST /auth/login-otp` - OTP login
- `POST /auth/refresh` - Refresh JWT
- `POST /auth/logout` - Logout & revoke tokens
- `GET /auth/google/callback` - Google OAuth callback

### Products

- `GET /products` - List products (filters, pagination)
- `GET /products/{id}` - Get product details
- `POST /admin/products` - Create product (admin)
- `PUT /admin/products/{id}` - Update product (admin)
- `DELETE /admin/products/{id}` - Delete product (admin)

### Cart & Orders

- `GET /cart` - Get cart
- `POST /cart/items` - Add to cart
- `PUT /cart/items/{item_id}` - Update quantity
- `DELETE /cart/items/{item_id}` - Remove from cart
- `POST /checkout` - Initiate checkout
- `GET /orders` - User order history
- `GET /orders/{id}` - Order details

### Payments

- `POST /payments/razorpay-webhook` - Razorpay webhook
- `POST /payments/verify` - Verify payment

### Social

- `GET /posts` - Feed
- `POST /posts` - Create post
- `PUT /posts/{id}` - Update post
- `DELETE /posts/{id}` - Delete post
- `POST /posts/{id}/like` - Like post
- `POST /posts/{id}/comment` - Comment
- `POST /posts/{id}/save` - Save post
- `GET /users/{id}` - User profile

### Admin

- `GET /admin/dashboard` - Analytics
- `GET /admin/orders` - All orders
- `GET /admin/posts/pending` - Moderation queue
- `PUT /admin/posts/{id}/approve` - Approve post
- `PUT /admin/posts/{id}/reject` - Reject post

## Environment Variables

See `.env.example` for complete list. Key variables:

```env
# Databases
POSTGRES_PASSWORD=xxx
MONGO_PASSWORD=xxx
REDIS_PASSWORD=xxx

# JWT
SECRET_KEY=xxx-change-in-production

# OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx

# Payments
RAZORPAY_KEY_ID=xxx
RAZORPAY_KEY_SECRET=xxx

# Media
IMAGEKIT_PRIVATE_KEY=xxx
IMAGEKIT_PUBLIC_KEY=xxx
IMAGEKIT_URL_ENDPOINT=xxx

# Email
SMTP_USER=xxx
SMTP_PASSWORD=xxx
```

## Security

- ✅ Password hashing with Argon2
- ✅ JWT with access/refresh tokens
- ✅ Token revocation via Redis JTI blocklist
- ✅ Rate limiting on auth endpoints
- ✅ CSRF protection patterns
- ✅ Secure HttpOnly cookies
- ✅ Webhook signature verification
- ✅ Optimistic/pessimistic locking for inventory

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add user_roles table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Development

### Type Checking

```bash
mypy app --strict
```

### Linting

```bash
pylint app
flake8 app
```

### Testing

```bash
pytest tests/ -v --cov=app --cov-report=html
```

## Deployment

1. Set production `.env` with real secrets
2. Set `ENV=production` in docker-compose
3. Use managed PostgreSQL, MongoDB, Redis
4. Enable HTTPS with Let's Encrypt on NGINX
5. Configure CloudFlare or CDN for static assets
6. Monitor logs with ELK or Datadog
