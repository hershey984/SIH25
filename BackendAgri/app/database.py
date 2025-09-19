import motor.motor_asyncio
from beanie import init_beanie
from app.config.settings import settings

# MongoDB client
mongodb_client = None

async def init_database():
    """Initialize MongoDB connection and Beanie ODM"""
    global mongodb_client
    
    try:
        # Create Motor client
        mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test connection
        await mongodb_client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Get database
        database = mongodb_client.get_default_database()
        
        # Import all models for Beanie initialization
        from app.models.chat import ChatSession, ChatMessage
        from app.models.knowledge import KnowledgeEntry
        from app.models.plant_doctor import PlantDoctorReport
        
        # Initialize Beanie with document models
        await init_beanie(
            database=database,
            document_models=[
                ChatSession,
                ChatMessage,
                KnowledgeEntry,
                PlantDoctorReport
            ]
        )
        
        print("✅ Beanie ODM initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise e

async def get_database():
    """Get MongoDB database instance"""
    if mongodb_client is None:
        raise Exception("Database not initialized. Call init_database() first.")
    return mongodb_client.get_default_database()

async def close_database():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        mongodb_client = None
        print("🔌 MongoDB connection closed")

# Health check function
async def check_database_health():
    """Check database connection health"""
    try:
        if mongodb_client is None:
            return {"status": "not_initialized"}
        
        # Ping database
        await mongodb_client.admin.command('ping')
        
        # Get database stats
        db = await get_database()
        stats = await db.command("dbStats")
        
        return {
            "status": "healthy",
            "database_name": db.name,
            "collections": stats.get("collections", 0),
            "data_size": stats.get("dataSize", 0),
            "storage_size": stats.get("storageSize", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    

get_db = get_database
