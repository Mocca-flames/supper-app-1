from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "DATABASE_URL"
    
    # Redis
    REDIS_URL: str = "REDIS_URL"
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"  # This will be overridden by firebase.json
    FIREBASE_CREDENTIALS_PATH: str = "firebase.json"
    
    # App Settings
    SECRET_KEY: str = "SECRET_KEY"
    DEBUG: bool = True
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
