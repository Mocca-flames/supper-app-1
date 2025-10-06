from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base

class DriverRating(Base):
    __tablename__ = "driver_ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(String, ForeignKey("drivers.driver_id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.client_id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False) # Added order_id
    rating = Column(Integer, nullable=False)  # 1 to 5 star rating
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", backref="ratings", foreign_keys=[driver_id])
    client = relationship("Client", backref="submitted_ratings", foreign_keys=[client_id])
    order = relationship("Order", backref="driver_rating", uselist=False) # Added order relationship

    # Constraint to ensure a client can only rate a specific order once.
    __table_args__ = (
        UniqueConstraint('order_id', name='_order_client_uc'),
    )