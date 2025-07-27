from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import computed_field

class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:5432/{self.POSTGRES_DB}"

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
