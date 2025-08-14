import pytest
from fastapi.testclient import TestClient
from app.main import app
import asyncio
import json
from unittest.mock import patch

# Mock Firebase initialization to avoid needing firebase.json
with patch('app.auth.firebase_auth.credentials.Certificate'):
    with patch('app.auth.firebase_auth.firebase_admin.initialize_app'):
        client = TestClient(app)

def test_websocket_connection():
    # Test basic WebSocket connection
    with client.websocket_connect("/ws/test_user") as websocket:
        # Send a test message
        websocket.send_text(json.dumps({
            "type": "test_message",
            "content": "Hello, WebSocket!"
        }))

        # Receive response
        data = websocket.receive_text()
        message = json.loads(data)

        assert message["type"] == "test_response"
        assert message["content"] == "Hello, WebSocket!"

def test_websocket_order_subscription():
    # Test order subscription functionality
    with client.websocket_connect("/ws/test_user") as websocket:
        # Subscribe to an order
        websocket.send_text(json.dumps({
            "type": "subscribe_order",
            "order_id": "test_order_123"
        }))

        # Receive subscription confirmation
        data = websocket.receive_text()
        message = json.loads(data)

        assert message["type"] == "subscribed"
        assert message["order_id"] == "test_order_123"

def test_websocket_order_tracking():
    # Test order tracking functionality
    with client.websocket_connect("/ws/track/test_order_123") as websocket:
        # Request order status
        websocket.send_text(json.dumps({
            "type": "get_status"
        }))

        # Receive status response
        data = websocket.receive_text()
        message = json.loads(data)

        assert message["type"] == "order_status"
        assert message["order_id"] == "test_order_123"
        assert "status" in message