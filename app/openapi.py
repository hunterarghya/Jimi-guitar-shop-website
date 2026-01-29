"""OpenAPI 3.0 specification generation."""
import json
from datetime import datetime

# OpenAPI 3.0 Specification for Jimi Platform
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Jimi - Guitar & Musical Instrument Shop API",
        "version": "1.0.0",
        "description": "Production-grade platform combining e-commerce, social media, admin dashboard, and chatbot",
        "contact": {
            "name": "Jimi Support",
            "email": "support@jimi.local",
        },
        "license": {
            "name": "MIT",
        },
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "http://localhost:80",
            "description": "Production server (via NGINX)",
        },
    ],
    "tags": [
        {
            "name": "auth",
            "description": "Authentication & Authorization",
        },
        {
            "name": "users",
            "description": "User Management",
        },
        {
            "name": "products",
            "description": "Product Catalog",
        },
        {
            "name": "cart",
            "description": "Shopping Cart",
        },
        {
            "name": "orders",
            "description": "Orders & Payments",
        },
        {
            "name": "social",
            "description": "Social Media (Posts, Comments, Likes, Saves)",
        },
        {
            "name": "moderation",
            "description": "Content Moderation",
        },
        {
            "name": "admin",
            "description": "Admin Dashboard & Management",
        },
        {
            "name": "chatbot",
            "description": "Chatbot & FAQ",
        },
    ],
    "paths": {
        "/health": {
            "get": {
                "summary": "Health Check",
                "tags": ["health"],
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "version": {"type": "string"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/v1/auth/register": {
            "post": {
                "summary": "Register new user",
                "tags": ["auth"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "phone": {"type": "string"},
                                    "password": {"type": "string", "minLength": 8},
                                    "full_name": {"type": "string"},
                                },
                                "required": ["email", "password"],
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "User registered successfully"},
                    "400": {"description": "Invalid request"},
                },
            }
        },
        "/api/v1/auth/login": {
            "post": {
                "summary": "Login user",
                "tags": ["auth"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "password": {"type": "string"},
                                },
                                "required": ["email", "password"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Login successful"},
                    "401": {"description": "Invalid credentials"},
                },
            }
        },
        "/api/v1/auth/refresh": {
            "post": {
                "summary": "Refresh access token",
                "tags": ["auth"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "refresh_token": {"type": "string"},
                                },
                                "required": ["refresh_token"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Token refreshed"},
                    "401": {"description": "Invalid token"},
                },
            }
        },
        "/api/v1/products": {
            "get": {
                "summary": "List products with filters",
                "tags": ["products"],
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "page_size", "in": "query", "schema": {"type": "integer"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "min_price", "in": "query", "schema": {"type": "number"}},
                    {"name": "max_price", "in": "query", "schema": {"type": "number"}},
                ],
                "responses": {
                    "200": {"description": "Products list"},
                },
            },
            "post": {
                "summary": "Create product (admin only)",
                "tags": ["products"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Product created"},
                    "403": {"description": "Forbidden"},
                },
            }
        },
        "/api/v1/products/search": {
            "get": {
                "summary": "Search products",
                "tags": ["products"],
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Search results"},
                },
            }
        },
        "/api/v1/cart": {
            "get": {
                "summary": "Get shopping cart",
                "tags": ["cart"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Cart items"},
                },
            },
            "delete": {
                "summary": "Clear shopping cart",
                "tags": ["cart"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Cart cleared"},
                },
            }
        },
        "/api/v1/cart/items": {
            "post": {
                "summary": "Add item to cart",
                "tags": ["cart"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Item added"},
                },
            }
        },
        "/api/v1/orders": {
            "post": {
                "summary": "Create order",
                "tags": ["orders"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Order created"},
                },
            },
            "get": {
                "summary": "Get user's orders",
                "tags": ["orders"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Orders list"},
                },
            }
        },
        "/api/v1/orders/{order_id}/verify-payment": {
            "post": {
                "summary": "Verify payment",
                "tags": ["orders"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Payment verified"},
                },
            }
        },
        "/api/v1/social/posts": {
            "get": {
                "summary": "Get posts feed",
                "tags": ["social"],
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                ],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Posts feed"},
                },
            },
            "post": {
                "summary": "Create post",
                "tags": ["social"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Post created"},
                },
            }
        },
        "/api/v1/social/posts/{post_id}/like": {
            "post": {
                "summary": "Like post",
                "tags": ["social"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Post liked"},
                },
            },
            "delete": {
                "summary": "Unlike post",
                "tags": ["social"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Post unliked"},
                },
            }
        },
        "/api/v1/social/posts/{post_id}/save": {
            "post": {
                "summary": "Save post",
                "tags": ["social"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Post saved"},
                },
            },
            "delete": {
                "summary": "Unsave post",
                "tags": ["social"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Post unsaved"},
                },
            }
        },
        "/api/v1/moderation/posts/{post_id}/report": {
            "post": {
                "summary": "Report post",
                "tags": ["moderation"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Post reported"},
                },
            }
        },
        "/api/v1/moderation/pending": {
            "get": {
                "summary": "Get pending moderation queue",
                "tags": ["moderation"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Pending posts"},
                },
            }
        },
        "/api/v1/admin/dashboard": {
            "get": {
                "summary": "Admin dashboard",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Dashboard metrics"},
                    "403": {"description": "Admin only"},
                },
            }
        },
        "/api/v1/admin/stats": {
            "get": {
                "summary": "Admin statistics",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Statistics"},
                    "403": {"description": "Admin only"},
                },
            }
        },
        "/api/v1/admin/discounts": {
            "get": {
                "summary": "List discounts",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Discounts list"},
                },
            },
            "post": {
                "summary": "Create discount",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Discount created"},
                },
            }
        },
        "/api/v1/admin/jobs": {
            "get": {
                "summary": "List job postings",
                "tags": ["admin"],
                "responses": {
                    "200": {"description": "Jobs list"},
                },
            },
            "post": {
                "summary": "Create job posting",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "Job created"},
                },
            }
        },
        "/api/v1/admin/deliveries": {
            "get": {
                "summary": "Get delivery queue",
                "tags": ["admin"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Delivery queue"},
                },
            }
        },
        "/api/v1/chatbot/chat": {
            "post": {
                "summary": "Chat with Jimi assistant",
                "tags": ["chatbot"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Chat response"},
                },
            }
        },
        "/api/v1/chatbot/start": {
            "post": {
                "summary": "Start conversation",
                "tags": ["chatbot"],
                "security": [{"bearer": []}],
                "responses": {
                    "200": {"description": "Conversation started"},
                },
            }
        },
        "/api/v1/chatbot/faqs": {
            "get": {
                "summary": "Get FAQs",
                "tags": ["chatbot"],
                "responses": {
                    "200": {"description": "FAQs list"},
                },
            },
            "post": {
                "summary": "Create FAQ",
                "tags": ["chatbot"],
                "security": [{"bearer": []}],
                "responses": {
                    "201": {"description": "FAQ created"},
                },
            }
        },
        "/api/v1/chatbot/faqs/search": {
            "get": {
                "summary": "Search FAQs",
                "tags": ["chatbot"],
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Search results"},
                },
            }
        },
    },
    "components": {
        "securitySchemes": {
            "bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token from /api/v1/auth/login",
            }
        },
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "status_code": {"type": "integer"},
                },
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "full_name": {"type": "string"},
                    "is_verified": {"type": "boolean"},
                    "is_admin": {"type": "boolean"},
                },
            },
            "Product": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "price": {"type": "number"},
                    "stock": {"type": "integer"},
                    "rating": {"type": "number"},
                },
            },
            "Order": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "items": {"type": "array"},
                    "total_amount": {"type": "number"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
            },
            "Post": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "content": {"type": "string"},
                    "images": {"type": "array"},
                    "likes_count": {"type": "integer"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
            },
        },
    },
}

def get_openapi_json():
    """Get OpenAPI specification as JSON."""
    return json.dumps(OPENAPI_SPEC, indent=2)

def get_openapi_yaml():
    """Get OpenAPI specification as YAML."""
    try:
        import yaml
        return yaml.dump(OPENAPI_SPEC, default_flow_style=False)
    except ImportError:
        import json
        return json.dumps(OPENAPI_SPEC, indent=2)
