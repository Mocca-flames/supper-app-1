import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/test_user"
    async with websockets.connect(uri) as websocket:
        # Send a test message
        await websocket.send(json.dumps({
            "type": "test_message",
            "content": "Hello, WebSocket!"
        }))

        # Receive response
        response = await websocket.recv()
        print(f"Received: {response}")

        # Parse and verify response
        message = json.loads(response)
        assert message["type"] == "test_response"
        assert message["content"] == "Hello, WebSocket!"
        print("Test passed!")

async def test_order_subscription():
    uri = "ws://localhost:8000/ws/test_user"
    async with websockets.connect(uri) as websocket:
        # Subscribe to an order
        await websocket.send(json.dumps({
            "type": "subscribe_order",
            "order_id": "test_order_123"
        }))

        # Receive subscription confirmation
        response = await websocket.recv()
        print(f"Received: {response}")

        # Parse and verify response
        message = json.loads(response)
        assert message["type"] == "subscribed"
        assert message["order_id"] == "test_order_123"
        print("Order subscription test passed!")

async def test_order_tracking():
    uri = "ws://localhost:8000/ws/track/test_order_123"
    async with websockets.connect(uri) as websocket:
        # Request order status
        await websocket.send(json.dumps({
            "type": "get_status"
        }))

        # Receive status response
        response = await websocket.recv()
        print(f"Received: {response}")

        # Parse and verify response
        message = json.loads(response)
        assert message["type"] == "order_status"
        assert message["order_id"] == "test_order_123"
        assert "status" in message
        print("Order tracking test passed!")

async def main():
    print("Testing WebSocket connection...")
    await test_websocket()

    print("\nTesting order subscription...")
    await test_order_subscription()

    print("\nTesting order tracking...")
    await test_order_tracking()

if __name__ == "__main__":
    asyncio.run(main())