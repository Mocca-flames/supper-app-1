from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PartnerDiscountBase(BaseModel):
    name: str
    discount_percent: int
    condition_text: Optional[str] = None
    is_active: bool = True

class PartnerDiscountCreate(PartnerDiscountBase):
    pass

class PartnerDiscountResponse(PartnerDiscountBase):
    id: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
