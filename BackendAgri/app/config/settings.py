import os
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "chatbot_db")
    MONGODB_MIN_CONNECTIONS: int = int(os.getenv("MONGODB_MIN_CONNECTIONS", "10"))
    MONGODB_MAX_CONNECTIONS: int = int(os.getenv("MONGODB_MAX_CONNECTIONS", "100"))
    MONGODB_MAX_IDLE_TIME_MS: int = int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "60000"))
    
    # MongoDB Atlas specific (if using cloud MongoDB)
    MONGODB_USERNAME: Optional[str] = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD: Optional[str] = os.getenv("MONGODB_PASSWORD")
    MONGODB_CLUSTER: Optional[str] = os.getenv("MONGODB_CLUSTER")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "false").lower() == "true"
    REDIS_DECODE_RESPONSES: bool = True
    
    # Session settings
    SESSION_EXPIRE_SECONDS: int = int(os.getenv("SESSION_EXPIRE_SECONDS", "3600"))  # 1 hour
    CHAT_HISTORY_LIMIT: int = int(os.getenv("CHAT_HISTORY_LIMIT", "100"))
    CHAT_HISTORY_CACHE_EXPIRE: int = int(os.getenv("CHAT_HISTORY_CACHE_EXPIRE", "1800"))  # 30 minutes
    
    # Google Cloud Storage
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "chatbot-storage")
    GCS_PROJECT_ID: Optional[str] = os.getenv("GCS_PROJECT_ID")
    
    # Google Cloud Authentication
    # Option 1: Service Account Key File
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Option 2: Service Account Key JSON (for containerized environments)
    GCS_SERVICE_ACCOUNT_KEY: Optional[str] = os.getenv("GCS_SERVICE_ACCOUNT_KEY")
    
    # GCS Settings
    GCS_UPLOAD_TIMEOUT: int = int(os.getenv("GCS_UPLOAD_TIMEOUT", "300"))  # 5 minutes
    GCS_DOWNLOAD_TIMEOUT: int = int(os.getenv("GCS_DOWNLOAD_TIMEOUT", "180"))  # 3 minutes
    GCS_MAX_FILE_SIZE_MB: int = int(os.getenv("GCS_MAX_FILE_SIZE_MB", "50"))
    GCS_ALLOWED_EXTENSIONS: str = os.getenv("GCS_ALLOWED_EXTENSIONS", "jpg,jpeg,png,pdf,txt,docx")
    
    # File storage paths in GCS bucket
    GCS_CHAT_IMAGES_PATH: str = os.getenv("GCS_CHAT_IMAGES_PATH", "chat-images/")
    GCS_PLANT_IMAGES_PATH: str = os.getenv("GCS_PLANT_IMAGES_PATH", "plant-diagnoses/")
    GCS_USER_UPLOADS_PATH: str = os.getenv("GCS_USER_UPLOADS_PATH", "user-uploads/")
    GCS_ARCHIVE_PATH: str = os.getenv("GCS_ARCHIVE_PATH", "archives/")
    
    # API Settings
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Chatbot Backend")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # FastAPI dev server
        "https://your-domain.com"  # Production domain
    ]
    
    # JWT/Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # AI/ML Settings (if using external AI services)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    # Plant Doctor specific settings
    PLANT_DIAGNOSIS_MODEL_PATH: str = os.getenv("PLANT_DIAGNOSIS_MODEL_PATH", "models/plant-diagnosis")
    MAX_PLANT_IMAGES_PER_DIAGNOSIS: int = int(os.getenv("MAX_PLANT_IMAGES_PER_DIAGNOSIS", "5"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    BURST_RATE_LIMIT: int = int(os.getenv("BURST_RATE_LIMIT", "10"))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def mongodb_url_with_auth(self) -> str:
        """Get MongoDB URL (handles both local and Atlas connections)"""
        # If MONGODB_URL already contains full connection string (Atlas format)
        if "mongodb+srv://" in self.MONGODB_URL or "mongodb://" in self.MONGODB_URL:
            # Check if database name is already in URL
            if "/" in self.MONGODB_URL.split("@")[-1] and "?" in self.MONGODB_URL:
                return self.MONGODB_URL
            elif "/" not in self.MONGODB_URL.split("@")[-1].split("?")[0]:
                # Add database name before query parameters
                if "?" in self.MONGODB_URL:
                    base_url, params = self.MONGODB_URL.split("?", 1)
                    return f"{base_url}/{self.MONGODB_DATABASE}?{params}"
                else:
                    return f"{self.MONGODB_URL}/{self.MONGODB_DATABASE}"
            return self.MONGODB_URL
        
        # Fallback for manual construction
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD and self.MONGODB_CLUSTER:
            # MongoDB Atlas format
            return f"mongodb+srv://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_CLUSTER}/{self.MONGODB_DATABASE}?retryWrites=true&w=majority"
        elif self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            # Local MongoDB with auth
            base_url = self.MONGODB_URL.replace("mongodb://", "")
            return f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{base_url}"
        else:
            # No authentication
            return f"{self.MONGODB_URL}/{self.MONGODB_DATABASE}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        scheme = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{scheme}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def gcs_allowed_extensions_list(self) -> list:
        """Get allowed file extensions as a list"""
        return [ext.strip().lower() for ext in self.GCS_ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def cors_origins(self) -> list:
        """Get CORS origins from environment or use defaults"""
        env_origins = os.getenv("BACKEND_CORS_ORIGINS")
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    def get_gcs_file_path(self, file_type: str, filename: str) -> str:
        """Generate GCS file path based on file type"""
        path_mapping = {
            "chat_image": self.GCS_CHAT_IMAGES_PATH,
            "plant_image": self.GCS_PLANT_IMAGES_PATH,
            "user_upload": self.GCS_USER_UPLOADS_PATH,
            "archive": self.GCS_ARCHIVE_PATH
        }
        
        base_path = path_mapping.get(file_type, self.GCS_USER_UPLOADS_PATH)
        return f"{base_path}{filename}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Validation helpers
def validate_mongodb_connection() -> bool:
    """Validate MongoDB connection settings"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_connection():
            client = AsyncIOMotorClient(settings.mongodb_url_with_auth)
            await client.server_info()
            client.close()
            return True
        
        return asyncio.run(test_connection())
    except Exception as e:
        print(f"MongoDB connection validation failed: {e}")
        return False

def validate_gcs_credentials() -> bool:
    """Validate Google Cloud Storage credentials"""
    try:
        from google.cloud import storage
        
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
        elif settings.GCS_SERVICE_ACCOUNT_KEY:
            import json
            import tempfile
            
            # Create temporary service account key file
            key_data = json.loads(settings.GCS_SERVICE_ACCOUNT_KEY)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(key_data, f)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
        
        client = storage.Client(project=settings.GCS_PROJECT_ID)
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        bucket.reload()  # Test access
        return True
        
    except Exception as e:
        print(f"GCS credentials validation failed: {e}")
        return False

# Environment-specific configurations
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
elif settings.ENVIRONMENT == "staging":
    settings.DEBUG = False
    settings.LOG_LEVEL = "INFO"
else:  # development
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"

@lru_cache
def get_settings() -> Settings:
    return Settings()
