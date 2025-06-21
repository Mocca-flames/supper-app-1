from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.websocket_service import connection_manager, WebSocketService
from ..auth.firebase_auth import FirebaseAuth
import json

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = None): # Added token query param
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        # You might want to verify the token here as well, depending on requirements
        # For example, ensuring user_id from path matches token's uid
        FirebaseAuth.verify_firebase_token(token) # Basic token validation
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
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
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)

@router.websocket("/ws/track/{order_id}")
async def track_order_websocket(websocket: WebSocket, order_id: str, token: str = None): # Added token query param
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Verify the Firebase token
        uid = FirebaseAuth.verify_firebase_token(token)
        # Optionally, you can add further checks here, e.g., if the user 'uid'
        # is authorized to track this specific 'order_id'.
        # For now, we'll just verify the token is valid.
    except HTTPException:
        # If token is invalid, close the connection before accepting
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    # Add the user (identified by uid from token) as a listener for this order_id
    # This assumes your connection_manager or similar service can handle this.
    # For simplicity, we'll just proceed if token is valid.
    # Example: connection_manager.subscribe_to_order_tracking(order_id, uid, websocket)

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
        # Example: connection_manager.unsubscribe_from_order_tracking(order_id, uid, websocket)
        pass
    finally:
        # Ensure connection is closed if not already
        # This part might be redundant if WebSocketDisconnect always triggers,
        # but can be a safeguard.
        # await websocket.close() # Be careful with closing already closed websockets
        pass
