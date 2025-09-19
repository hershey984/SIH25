from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis  # Use async version
import motor.motor_asyncio
from beanie import init_beanie

from app.config.settings import settings
from app.routes import chat, storage
# Import your models for Beanie initialization
from app.models.chat import ChatMessage, ChatSession
from app.models.knowledge import KnowledgeBase, KnowledgeEntry
from app.models.plant_doctor import PlantDoctorReport

# MongoDB client
mongodb_client = None

# Initialize database and connections on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongodb_client
    
    # Startup
    try:
        # Initialize MongoDB connection
        mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test MongoDB connection
        await mongodb_client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Get database
        database = mongodb_client.get_default_database()
        
        # Initialize Beanie with document models
        await init_beanie(
            database=database,
            document_models=[
                ChatMessage,
                ChatSession,
                KnowledgeBase,
                KnowledgeEntry,
                PlantDoctorReport
            ]
        )
        print("✅ Beanie ODM initialized successfully")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise e
    
    # Test Redis connection
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        await r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        # Don't raise here if Redis is optional
    
    print("🚀 Agriculture Chatbot Backend started successfully")
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()
        print("🔌 MongoDB connection closed")
    
    print("🛑 Shutting down Agriculture Chatbot Backend")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered agriculture assistance backend with MongoDB and Redis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if hasattr(settings, 'ALLOWED_ORIGINS') and settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["Chat"])
app.include_router(storage.router, prefix=settings.API_V1_STR, tags=["Storage"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {}
    }
    
    # Test MongoDB connection
    try:
        if mongodb_client:
            await mongodb_client.admin.command('ping')
            health_status["services"]["mongodb"] = "healthy"
        else:
            health_status["services"]["mongodb"] = "not_initialized"
    except Exception as e:
        health_status["services"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Test Redis connection
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        r.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Agriculture Chatbot Backend API",
        "version": "1.0.0",
        "description": "AI-powered agriculture assistance platform",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Dependency to get database
async def get_database():
    """Get MongoDB database instance"""
    if mongodb_client is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return mongodb_client.get_default_database()

# Dependency to get Redis client
def get_redis():
    """Get Redis client instance"""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url)
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": "Internal server error",
        "status_code": 500,
        "path": str(request.url)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )