# WebSocket Tracking Guide

## Overview
This guide provides essential information about the WebSocket endpoints for real-time order tracking.

## Endpoints

### 1. Driver WebSocket Endpoint
**URL:** `ws://your-server.com/ws/{user_id}`

**Path Parameters:**
- `user_id`: Unique identifier for the driver

**Message Types:**

#### Location Update (Driver → Server)
```json
{
  "type": "driver_location_update",
  "latitude": 34.0522,
  "longitude": -118.2437
}
```

#### Subscribe to Order (Driver → Server)
```json
{
  "type": "subscribe_order",
  "order_id": "order_abc_123"
}
```

**Response (Server → Driver):**
```json
{
  "type": "subscribed",
  "order_id": "order_abc_123"
}
```

### 2. Order Tracking WebSocket Endpoint
**URL:** `ws://your-server.com/ws/track/{order_id}`

**Path Parameters:**
- `order_id`: ID of the order to track

**Message Types:**

#### Get Status (Client → Server)
```json
{
  "type": "get_status"
}
```

**Response (Server → Client):**
```json
{
  "type": "order_status",
  "order_id": "order_abc_123",
  "status": "in_transit"
}
```

## Implementation Notes

### Driver Side
1. Connect to `ws://your-server.com/ws/{driver_id}`
2. Send location updates with `driver_location_update` message type
3. Subscribe to orders with `subscribe_order` message type

### Client Side
1. Connect to `ws://your-server.com/ws/track/{order_id}`
2. Request status updates with `get_status` message type
3. Receive real-time updates from the server

## Security (MVP)
- Use `wss://` for secure connections in production
- Basic validation of message formats
- No authentication for MVP development and testing
