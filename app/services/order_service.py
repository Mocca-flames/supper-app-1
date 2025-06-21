from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from ..models.order_models import Order, OrderStatus
from ..schemas.order_schemas import OrderCreate, OrderAccept
from ..utils.redis_client import RedisService

class OrderService:
    @staticmethod
    def create_order(db: Session, order_data: OrderCreate) -> Order:
        order = Order(
            client_id=order_data.client_id,
            order_type=order_data.order_type,
            pickup_address=order_data.pickup_address,
            pickup_latitude=order_data.pickup_latitude,
            pickup_longitude=order_data.pickup_longitude,
            dropoff_address=order_data.dropoff_address,
            dropoff_latitude=order_data.dropoff_latitude,
            dropoff_longitude=order_data.dropoff_longitude,
            special_instructions=order_data.special_instructions,
            patient_details=order_data.patient_details,
            medical_items=order_data.medical_items
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Cache order status in Redis
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def get_pending_orders(db: Session) -> List[Order]:
        return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()
    
    @staticmethod
    def accept_order(db: Session, order_id: str, accept_data: OrderAccept) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        if order.status != OrderStatus.PENDING:
            raise ValueError("Order already accepted or completed")
        
        order.driver_id = accept_data.driver_id
        order.status = OrderStatus.ACCEPTED
        order.price = accept_data.estimated_price
        
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def update_order_status(db: Session, order_id: str, new_status: OrderStatus) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        
        order.status = new_status
        db.commit()
        db.refresh(order)
        
        # Update Redis cache
        RedisService.set_order_status(order.id, order.status.value)
        
        return order
    
    @staticmethod
    def get_client_orders(db: Session, client_id: str) -> List[Order]:
        return db.query(Order).filter(Order.client_id == client_id).all()
    
    @staticmethod
    def get_driver_orders(db: Session, driver_id: str) -> List[Order]:
        return db.query(Order).filter(Order.driver_id == driver_id).all()

    @staticmethod
    def get_all_orders(db: Session) -> List[Order]:
        return db.query(Order).all()
