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


    # PayFast Payment Gateway Configuration
    PAYFAST_ENVIRONMENT: str = "sandbox"  # or "production"
    PAYFAST_MERCHANT_ID: str = "31793961"
    PAYFAST_MERCHANT_KEY: str = "kuno3nwljlr52"
    PAYFAST_SANDBOX_URL: str = "https://sandbox.payfast.co.za"
    PAYFAST_PRODUCTION_URL: str = "https://www.payfast.co.za"

    # Paystack Payment Gateway Configuration
    PAYSTACK_SECRET_KEY: str = "sk_test_566a7b362057bc2ca80df97ec482290d60180ea4"
    PAYSTACK_PUBLIC_KEY: str = "pk_test_eb846621ad62bc7df0027794c88969c04f075b06"
    PAYSTACK_ENVIRONMENT: str = "sandbox"  # or "production"


# Create a singleton instance of Settings
settings = Settings()
