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
    CACHE_TTL_ROUTES: int = 3600 # Default TTL for route caches (1 hour)
    CACHE_TTL_GEOCODING: int = 86400 # Default TTL for geocoding caches (24 hours)
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "your-firebase-project-id"  # This will be overridden by firebase.json
    FIREBASE_CREDENTIALS_PATH: str = "firebase.json"
    
    # App Settings
    SECRET_KEY: str = "SECRET_KEY"
    DEBUG: bool = True

    # MapBox Configuration
    MAPBOX_ACCESS_TOKEN: str
    MAPBOX_BASE_URL: str = "https://api.mapbox.com"
    MAPBOX_API_VERSION: str = "v5"

    # Rate Limiting
    MAPBOX_REQUESTS_PER_MINUTE: int = 600
    MAPBOX_REQUESTS_PER_HOUR: int = 30000

    # Timeout Configuration
    MAPBOX_REQUEST_TIMEOUT: int = 10
    MAPBOX_RETRY_ATTEMPTS: int = 3
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
