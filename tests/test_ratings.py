import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from app.main import app
from app.models.user_models import Driver, Client
from app.models.order_models import Order, OrderStatus
from app.models.rating_models import DriverRating
from app.schemas.rating_schemas import DriverRatingCreate
from app.database import Base, engine
from app.auth.middleware import get_current_client_id # Assuming this is used for dependency override

# Use the test client
client = TestClient(app)

# Mock dependencies for testing
def override_get_current_client_id():
    """Returns a fixed client ID for testing authenticated routes."""
    return "test_client_id"

app.dependency_overrides[get_current_client_id] = override_get_current_client_id

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Ensure tables are created for testing."""
    # Note: In a real test setup, you'd typically use a separate test database.
    # Assuming Base.metadata.create_all(bind=engine) is sufficient for this environment.
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_driver(db: Session):
    """Fixture for a test driver."""
    driver = Driver(driver_id="test_driver_id", license_no="12345", vehicle_type="car")
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@pytest.fixture
def test_client_user(db: Session):
    """Fixture for a test client user."""
    client_user = Client(client_id="test_client_id", home_address="123 Test St")
    db.add(client_user)
    db.commit()
    db.refresh(client_user)
    return client_user

@pytest.fixture
def completed_order(db: Session, test_driver, test_client_user):
    """Fixture for a completed order ready for rating."""
    order = Order(
        id="test_order_id_1",
        client_id=test_client_user.client_id,
        driver_id=test_driver.driver_id,
        order_type=OrderStatus.COMPLETED, # Using OrderStatus enum value for simplicity
        status=OrderStatus.COMPLETED,
        pickup_address="A",
        dropoff_address="B"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def test_submit_driver_rating_success(db: Session, test_driver, test_client_user, completed_order):
    """Test successful submission of a driver rating."""
    rating_data = DriverRatingCreate(
        driver_id=test_driver.driver_id,
        order_id=completed_order.id,
        rating=5
    )
    
    response = client.post(
        "/api/ratings/drivers",
        json=rating_data.dict()
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["driver_id"] == test_driver.driver_id
    assert data["order_id"] == completed_order.id
    assert data["rating"] == 5
    
    # Verify rating exists in DB
    db_rating = db.query(DriverRating).filter(DriverRating.order_id == completed_order.id).first()
    assert db_rating is not None
    assert db_rating.rating == 5

def test_submit_driver_rating_order_not_completed(db: Session, test_driver, test_client_user):
    """Test submission failure if order is not completed."""
    pending_order = Order(
        id="test_order_id_pending",
        client_id=test_client_user.client_id,
        driver_id=test_driver.driver_id,
        order_type=OrderStatus.PENDING,
        status=OrderStatus.PENDING,
        pickup_address="C",
        dropoff_address="D"
    )
    db.add(pending_order)
    db.commit()
    
    rating_data = DriverRatingCreate(
        driver_id=test_driver.driver_id,
        order_id=pending_order.id,
        rating=4
    )
    
    response = client.post(
        "/api/ratings/drivers",
        json=rating_data.dict()
    )
    
    assert response.status_code == 400
    assert "Order status must be 'completed'" in response.json()["detail"]

def test_submit_driver_rating_already_rated(db: Session, test_driver, test_client_user, completed_order):
    """Test submission failure if order is already rated."""
    # First rating (already submitted in test_submit_driver_rating_success if run first, but let's ensure it here)
    first_rating = DriverRating(
        driver_id=test_driver.driver_id,
        client_id=test_client_user.client_id,
        order_id=completed_order.id,
        rating=5
    )
    db.add(first_rating)
    db.commit()
    
    # Second attempt
    rating_data = DriverRatingCreate(
        driver_id=test_driver.driver_id,
        order_id=completed_order.id,
        rating=1
    )
    
    response = client.post(
        "/api/ratings/drivers",
        json=rating_data.dict()
    )
    
    assert response.status_code == 409
    assert "This order has already been rated." in response.json()["detail"]

def test_get_driver_average_rating_success(db: Session, test_driver, test_client_user):
    """Test retrieval of average rating."""
    driver_id = test_driver.driver_id
    
    # Create multiple ratings for the driver
    ratings_data = [5, 4, 5]
    
    # Create dummy orders for the ratings
    for i, rating_val in enumerate(ratings_data):
        order = Order(
            id=f"avg_order_{i}",
            client_id=test_client_user.client_id,
            driver_id=driver_id,
            order_type=OrderStatus.COMPLETED,
            status=OrderStatus.COMPLETED,
            pickup_address=f"P{i}",
            dropoff_address=f"D{i}"
        )
        db.add(order)
        db.flush()
        
        rating = DriverRating(
            driver_id=driver_id,
            client_id=test_client_user.client_id,
            order_id=order.id,
            rating=rating_val
        )
        db.add(rating)
    db.commit()
    
    expected_avg = round((5 + 4 + 5) / 3, 2)
    
    response = client.get(f"/api/ratings/drivers/{driver_id}/average")
    
    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == driver_id
    assert data["average_rating"] == expected_avg
    assert data["total_ratings"] == 3

def test_get_driver_average_rating_no_ratings(db: Session, test_driver):
    """Test retrieval of average rating when no ratings exist."""
    driver_id = test_driver.driver_id
    
    response = client.get(f"/api/ratings/drivers/{driver_id}/average")
    
    assert response.status_code == 200
    data = response.json()
    assert data["driver_id"] == driver_id
    assert data["average_rating"] is None
    assert data["total_ratings"] == 0

def test_get_driver_average_rating_non_existent_driver():
    """Test retrieval of average rating for a non-existent driver."""
    response = client.get("/api/ratings/drivers/non_existent_driver/average")
    
    assert response.status_code == 404
    assert "Driver not found." in response.json()["detail"]