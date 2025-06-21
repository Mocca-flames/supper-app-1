# Driver Guide

## API Endpoints

### Admin Endpoints

- **Create Order**
  - **Endpoint:** `/admin/orders`
  - **Method:** `POST`
  - **Description:** Admin creates an order for a specific client.
  - **Request Model:** `AdminOrderCreate`
  - **Response Model:** `OrderResponse`

## WebSockets

### Admin WebSockets

- **WebSocket Endpoint:** `/ws/{user_id}`
  - **Description:** General WebSocket endpoint for user-specific communications.
  - **Message Types:**
    - `subscribe_order`: Subscribe to order updates.
    - `driver_location_update`: Handle driver location updates.

- **WebSocket Endpoint:** `/ws/track/{order_id}`
  - **Description:** WebSocket endpoint for tracking order status.
  - **Message Types:**
    - `get_status`: Get current order status.

## Guide to Log In and Create Orders

### Logging In

Authentication is handled via Firebase using Google Sign-In. The application will receive a Firebase ID token from the client, which should be sent in the Authorization header as a Bearer token.

1. **Client-side:** User signs in with Google via Firebase.
2. **Client-side:** Firebase returns an ID token.
3. **API Request:** Include the ID token in the `Authorization` header:
   ```
   Authorization: Bearer <FIREBASE_ID_TOKEN>
   ```
   The backend will verify this token to authenticate the user.

### Creating Orders

1. **Endpoint:** `/admin/orders`
2. **Method:** `POST`
3. **Request Body:**
   ```json
   {
     "client_id": "client_123",
     "order_details": {
       "item": "Pizza",
       "quantity": 2,
       "price": 20.00
     }
   }
   ```
4. **Response:**
   ```json
   {
     "order_id": "order_123",
     "status": "pending",
     "order_details": {
       "item": "Pizza",
       "quantity": 2,
       "price": 20.00
     }
   }
   ```

## Tracking Orders

1. **WebSocket Endpoint:** `/ws/track/{order_id}`
2. **Message Type:** `get_status`
3. **Response:**
   ```json
   {
     "type": "order_status",
     "order_id": "order_123",
     "status": "in_progress"
   }
   ```

## Additional Notes


- Use the WebSocket endpoints to handle real-time updates and communications.
