from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from ..database import Base

class PartnerDiscount(Base):
    __tablename__ = "partner_discounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # Company/Event name
    discount_percent = Column(Integer, nullable=False)  # 30 = 30%
    condition_text = Column(Text, nullable=True)  # "to location = Event B"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
