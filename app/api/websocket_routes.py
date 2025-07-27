from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..database import get_db
from ..services.websocket_service import connection_manager, WebSocketService
from ..services.order_service import OrderService # Import OrderService
from ..auth.firebase_auth import FirebaseAuth
from ..models.order_models import OrderStatus # Import OrderStatus
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str = None, db: Session = Depends(get_db)):
    if not token:
        logger.warning(f"WebSocket connection denied for {user_id}: No token provided.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        # Verify the token and ensure user_id from path matches token's uid
        decoded_token = FirebaseAuth.verify_firebase_token(token)
        if decoded_token['uid'] != user_id:
            logger.warning(f"WebSocket connection denied for {user_id}: Token UID mismatch.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except HTTPException as e:
        logger.error(f"WebSocket connection denied for {user_id}: Token verification failed: {e.detail}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "subscribe_order":
                order_id = message.get("order_id")
                if order_id:
                    # Optional: Verify if user_id is authorized to track this order_id
                    order = OrderService.get_order_by_id(db, order_id)
                    if not order or (order.client_id != user_id and order.driver_id != user_id):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Unauthorized to subscribe to this order."
                        }))
                        continue

                    connection_manager.subscribe_to_order(order_id, user_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "order_id": order_id
                    }))
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Missing order_id for subscription."}))
            
            elif message_type == "driver_location_update":
                # This message type should typically come from a driver's device
                # For simplicity, assuming user_id is the driver_id here.
                # In a real app, you'd have separate driver-specific auth/endpoints.
                latitude = message.get("latitude")
                longitude = message.get("longitude")
                if latitude is not None and longitude is not None:
                    await WebSocketService.broadcast_driver_location(db, user_id, latitude, longitude)
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Missing latitude or longitude for driver location update."}))
            
            elif message_type == "get_order_status":
                order_id = message.get("order_id")
                if order_id:
                    current_status = OrderService.get_order_by_id(db, order_id)
                    if current_status:
                        await websocket.send_text(json.dumps({
                            "type": "order_status",
                            "order_id": order_id,
                            "status": current_status.status.value,
                            "estimated_duration": current_status.estimated_duration,
                            "estimated_distance": current_status.estimated_distance,
                            "calculated_eta": current_status.calculated_eta,
                            "route_geometry": current_status.route_geometry
                        }))
                    else:
                        await websocket.send_text(json.dumps({"type": "error", "message": "Order not found."}))
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Missing order_id for status request."}))

            else:
                logger.warning(f"Received unknown message type from {user_id}: {message_type}")
                await websocket.send_text(json.dumps({"type": "error", "message": "Unknown message type."}))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

# The /ws/track/{order_id} endpoint is now redundant as /ws/{user_id} can handle subscriptions.
# If specific tracking logic is needed, it can be integrated into the main websocket_endpoint
# or kept as a separate, more specialized endpoint. For now, we'll remove it as the plan
# focuses on enhancing the existing WebSocket for real-time features.
# @router.websocket("/ws/track/{order_id}")
# async def track_order_websocket(websocket: WebSocket, order_id: str, token: str = None):
#     ... (removed as per plan's consolidation)
