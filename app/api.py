"""Main FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import logging.config
from pathlib import Path

from app.core import (
    get_settings,
    init_pg,
    init_mongo,
    init_redis,
    close_connections,
)
from app.middleware import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.products.router import router as products_router
from app.modules.cart.router import router as cart_router
from app.modules.orders.router import router as orders_router
from app.modules.social.router import router as social_router
from app.modules.moderation.router import router as moderation_router
from app.modules.admin.router import router as admin_router
from app.modules.chatbot.router import router as chatbot_router

# Configure logging
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
})

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting up Jimi platform...")
    settings = get_settings()
    
    try:
        await init_pg(settings)
        await init_mongo(settings)
        await init_redis(settings)
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_connections()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host Middleware
    allowed_hosts = ["localhost", "127.0.0.1", "testserver"]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )
    
    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}
    
    # Include routers here (will be added in Step 2 onwards)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(products_router)
    app.include_router(cart_router)
    app.include_router(orders_router)
    app.include_router(social_router)
    app.include_router(moderation_router)
    app.include_router(admin_router)
    app.include_router(chatbot_router)
    
    # Mount frontend static files at root (MUST be after all API routers)
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    
    logger.info("FastAPI app initialized successfully")
    
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
