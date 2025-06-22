import logging
from contextlib import asynccontextmanager # Added for lifespan
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text # Added for text() construct
from .database import engine, get_db
from .models import user_models, order_models, discount_models
from .auth import firebase_auth  # Initializes Firebase Admin SDK (via app.auth.firebase_auth)
from .api import auth_routes, client_routes, driver_routes, admin_routes, websocket_routes, order_routes # Added order_routes
from .utils.redis_client import redis_client
from .config import settings
import uvicorn
import firebase_admin # Added for Firebase details

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
user_models.Base.metadata.create_all(bind=engine)
order_models.Base.metadata.create_all(bind=engine)
discount_models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Application startup initiated via lifespan manager.")
    try:
        # Log Firebase initialization details
        # Firebase is initialized when firebase_auth module is imported.
        default_app = firebase_admin.get_app()
        logger.info(f"Firebase App initialized: {default_app.name}, Project ID: {default_app.project_id}")
    except Exception as e:
        logger.error(f"Error getting Firebase app details: {e}")

    try:
        if redis_client.ping():
            logger.info("Successfully connected to Redis on startup.")
        else:
            logger.warning("Could not ping Redis on startup. Health check will report status.")
    except Exception as e:
        logger.error(f"Redis connection error on startup: {e}")
    
    logger.info("Application startup complete.")
    yield
    # Shutdown logic
    logger.info("Application shutting down via lifespan manager.")


app = FastAPI(
    title="Supper Delivery API",
    description="Multi-service delivery platform for food, parcels, medical items, and rides",
    version="1.0.0",
    lifespan=lifespan  # Added lifespan manager
)

# CORS middleware for mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(client_routes.router, prefix="/api")
app.include_router(driver_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(order_routes.router, prefix="/api") # Added order_routes
app.include_router(websocket_routes.router)

@app.get("/")
def read_root():
    return {"message": "Supper Delivery API v1.0.0"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_status = "unknown"
    redis_status = "unknown"

    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        database_status = "disconnected"

    try:
        # Test Redis connection
        if redis_client.ping():
            redis_status = "connected"
        else:
            redis_status = "disconnected"
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        redis_status = "disconnected"

    if database_status == "disconnected" or redis_status == "disconnected":
        logger.warning(f"Health check failed: DB status '{database_status}', Redis status '{redis_status}'")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "database": database_status,
            "redis": redis_status
        })
    return {"status": "healthy", "database": database_status, "redis": redis_status}

if __name__ == "__main__":
    # APP_HOST and APP_PORT should be defined in app.config.settings
    # Defaulting to "0.0.0.0" and 8000 if not set in config.
    uvicorn.run(
        app,
        host=getattr(settings, "APP_HOST", "0.0.0.0"),
        port=getattr(settings, "APP_PORT", 8080)
    )
