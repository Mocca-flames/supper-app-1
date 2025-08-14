from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_service import connection_manager, WebSocketService
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "subscribe_order":
                order_id = message.get("order_id")
                connection_manager.subscribe_to_order(order_id, user_id)
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "order_id": order_id
                }))

            elif message.get("type") == "driver_location_update":
                # Handle driver location updates
                latitude = message.get("latitude")
                longitude = message.get("longitude")
                await WebSocketService.broadcast_driver_location(user_id, latitude, longitude)

            elif message.get("type") == "test_message":
                # Handle test message
                await websocket.send_text(json.dumps({
                    "type": "test_response",
                    "content": message.get("content", "")
                }))

    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)

@router.websocket("/ws/track/{order_id}")
async def track_order_websocket(websocket: WebSocket, order_id: str):
    await websocket.accept()

    try:
        while True:
            # Send periodic updates about order status
            data = await websocket.receive_text() # Client can send messages, e.g., to confirm it's still active
            message = json.loads(data)

            if message.get("type") == "get_status":
                # Get current order status (this part remains the same)
                from ..utils.redis_client import RedisService
                current_status = RedisService.get_order_status(order_id) # Renamed variable for clarity
                await websocket.send_text(json.dumps({
                    "type": "order_status",
                    "order_id": order_id,
                    "status": current_status
                }))
            # You might want to handle other message types or just keep the connection alive

    except WebSocketDisconnect:
        # Clean up resources if necessary
        pass
    finally:
        # Ensure connection is closed if not already
        pass
