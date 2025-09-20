import pytest
from sqlalchemy.orm import Session
from app.services.order_service import OrderService
from app.models.order_models import Order
from app.models.payment_models import Payment, Refund
from app.models.user_models import User
from decimal import Decimal

@pytest.fixture
def setup_orders_payments(db: Session):
    # Create a test user
    user = User(id="test-client-1", email="testclient@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create orders for the user
    order1 = Order(
        id="order-1",
        client_id=user.id,
        order_type="ride",
        pickup_address="123 Test St",
        dropoff_address="456 Test Ave",
        distance_km=Decimal("10.0"),
        price=Decimal("100.00")
    )
    order2 = Order(
        id="order-2",
        client_id=user.id,
        order_type="food_delivery",
        pickup_address="789 Test Blvd",
        dropoff_address="101 Test Rd",
        distance_km=Decimal("5.0"),
        price=Decimal("50.00")
    )
    db.add_all([order1, order2])
    db.commit()

    # Create payments linked to orders
    payment1 = Payment(
        id="payment-1",
        order_id=order1.id,
        user_id=user.id,
        payment_type="client_payment",
        amount=Decimal("100.00"),
        payment_method="cash",
        status="completed"
    )
    payment2 = Payment(
        id="payment-2",
        order_id=order2.id,
        user_id=user.id,
        payment_type="client_payment",
        amount=Decimal("50.00"),
        payment_method="cash",
        status="completed"
    )
    db.add_all([payment1, payment2])
    db.commit()

    # Create refunds linked to payments and orders
    refund1 = Refund(
        id="refund-1",
        payment_id=payment1.id,
        order_id=order1.id,
        amount=Decimal("20.00"),
        status="pending"
    )
    db.add(refund1)
    db.commit()

    yield user.id

    # Cleanup after test
    db.query(Refund).delete()
    db.query(Payment).delete()
    db.query(Order).delete()
    db.query(User).delete()
    db.commit()

def test_delete_all_orders_for_user_with_related_data(db: Session, setup_orders_payments):
    client_id = setup_orders_payments

    # Confirm orders exist before deletion
    orders_before = db.query(Order).filter(Order.client_id == client_id).count()
    assert orders_before == 2

    # Call the deletion method
    result = OrderService.delete_all_orders_for_user(db, client_id)

    # Confirm deletion success
    assert result["success"] is True
    assert result["orders_deleted"] == 2
    assert result["payments_deleted"] >= 2
    assert result["refunds_deleted"] >= 1

    # Confirm no orders remain
    orders_after = db.query(Order).filter(Order.client_id == client_id).count()
    assert orders_after == 0

def test_delete_all_orders_for_user_no_orders(db: Session):
    # Use a client_id with no orders
    client_id = "nonexistent-client"
    result = OrderService.delete_all_orders_for_user(db, client_id)
    assert result["success"] is True
    assert result["orders_found"] == 0
    assert result["orders_deleted"] == 0