from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import uuid

class DriverRatingBase(BaseModel):
    driver_id: str = Field(..., description="Firebase UID of the driver being rated.")
    order_id: str = Field(..., description="ID of the completed order being rated.")
    rating: int = Field(..., description="Star rating (1 to 5).", ge=1, le=5)

class DriverRatingCreate(DriverRatingBase):
    pass

class DriverRatingResponse(DriverRatingBase):
    id: uuid.UUID
    client_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class DriverAverageRating(BaseModel):
    driver_id: str
    average_rating: Optional[float] = Field(None, description="Average star rating of the driver.")
    total_ratings: int = Field(..., description="Total number of ratings received.")