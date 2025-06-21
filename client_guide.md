# Client-Only Application Backend Integration Guide

## 1. Introduction

This guide outlines how the client-only application (e.g., mobile app, flutter android) should interact with the backend API and WebSocket services. The primary goal is to enable clients to authenticate, create and track orders, and monitor driver locations in real-time.

## 2. Authentication with Firebase

Firebase Authentication will be used to manage client identities. Each client will have a unique Firebase UID, which serves as their `client_id`.

### 2.1. Authentication Flow:

1.  **Client-Side Firebase SDK**: The client application should integrate the Firebase Authentication SDK (for flutter android).
2.  **Sign-Up/Sign-In**: Clients will sign up or sign in using Firebase supported methods (e.g., Google, Apple, phone number).
3.  **Firebase ID Token**: Upon successful authentication, Firebase provides an ID Token to the client.
4.  **Backend Verification**: This ID Token must be sent by the client in the `Authorization` header (as a Bearer token) with every API request to secured backend endpoints.
    *   Example Header: `Authorization: Bearer <FIREBASE_ID_TOKEN>`
5.  **Backend User Creation/Lookup**:
    *   The backend API (likely via `app/api/auth_routes.py` and `app/auth/firebase_auth.py`) will verify the ID Token.
    *   If the token is valid, the backend will extract the Firebase UID.
    *   The backend will then either retrieve the existing user associated with this UID or create a new user record in the application's database (e.g., in `user_models.py`) if it's their first interaction.

### 2.2. Securing API Requests:

*   All client-specific API endpoints (e.g., creating orders, fetching order history) must be protected and require a valid Firebase ID Token.
*   The backend middleware (e.g., `app/auth/middleware.py`) should handle token verification for relevant routes.

## 3. Order Management

Clients can create new orders and track their existing orders.

### 3.1. Creating a New Order:

*   **Endpoint**: Likely `POST /api/client/orders/` (refer to `app/api/client_routes.py`).
*   **Request Body**: The client sends order details. This might include:
    ```json
    {
      "pickup_location": {"latitude": 34.0522, "longitude": -118.2437, "address": "123 Main St"},
      "dropoff_location": {"latitude": 34.0523, "longitude": -118.2438, "address": "456 Oak St"},
      "items": [
        {"name": "Item 1", "quantity": 1, "price": 10.00},
        {"name": "Item 2", "quantity": 2, "price": 5.00}
      ],
      "payment_method_id": "stripe_payment_method_id_example", // Or other payment details
      "notes": "Optional notes for the driver."
    }
    ```
    *(Schema likely defined in `app/schemas/order_schemas.py`)*
*   **Authentication**: Requires Firebase ID Token.
*   **Response**: Upon successful creation, the API returns the newly created order details, including an `order_id`.
    ```json
    {
      "order_id": "unique_order_identifier",
      "client_id": "firebase_uid",
      "status": "pending_confirmation", // Initial status
      // ... other order details
    }
    ```

### 3.2. Viewing Order History:

*   **Endpoint**: Likely `GET /api/client/orders/` (refer to `app/api/client_routes.py`).
*   **Authentication**: Requires Firebase ID Token.
*   **Response**: Returns a list of orders placed by the authenticated client.
    ```json
    [
      {
        "order_id": "order_id_1",
        "status": "delivered",
        // ... other details
      },
      {
        "order_id": "order_id_2",
        "status": "out_for_delivery",
        // ... other details
      }
    ]
    ```

### 3.3. Tracking Order Status:

*   **Via API**: Clients can poll `GET /api/client/orders/{order_id}` for status updates.
*   **Via WebSocket**: For real-time updates, clients should subscribe to order status changes through the WebSocket connection (see Section 5).
    *   The client would subscribe to a topic like `order_updates:{order_id}`.
    *   The backend (e.g., `app/services/order_service.py` and `app/api/websocket_routes.py`) would publish status changes (e.g., "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled") to this topic.

## 4. Real-time Driver Tracking

Clients can track the assigned driver's location in real-time once an order is "out_for_delivery".

### 4.1. How it Works:

1.  **Driver Location Updates**: The driver's application periodically sends its current latitude and longitude to the backend (likely via `app/api/driver_routes.py` or a dedicated WebSocket for drivers).
2.  **Backend Processing**: The backend (e.g., `app/services/driver_service.py`) stores/updates the driver's current location, associating it with their active order.
3.  **Client Subscription**: The client application, upon an order becoming "out_for_delivery", subscribes to a WebSocket topic for driver location updates related to their specific order.
    *   Example Topic: `driver_location:{order_id}` or `driver_location:{driver_id}` (if the client knows the driver_id).
4.  **WebSocket Broadcast**: The backend's WebSocket service (e.g., `app/api/websocket_routes.py` and `app/services/websocket_service.py`) broadcasts the driver's updated latitude/longitude to subscribed clients on this topic.

### 4.2. Using Latitude/Longitude Data:

*   The client application receives `{"latitude": Y, "longitude": X}` coordinates.
*   This data is used to update the driver's marker on an integrated map (e.g., Google Maps, Mapbox, Leaflet).
*   The client can also calculate Estimated Time of Arrival (ETA) based on driver location and destination, though this logic might also be provided by the backend.

## 5. WebSocket Integration

WebSockets are crucial for real-time communication (order status updates, driver tracking).

### 5.1. Establishing a Connection:

*   **Endpoint**: The client connects to the WebSocket server, e.g., `ws://yourdomain.com/ws/{firebase_id_token}` or `wss://yourdomain.com/ws/{firebase_id_token}`. The token is used for authenticating the WebSocket session. (Refer to `app/api/websocket_routes.py`).
*   The backend will validate the `firebase_id_token` before establishing the connection.

### 5.2. Subscribing to Events:

Once connected, the client needs to send messages to subscribe to specific events/topics. The exact message format for subscription depends on the backend implementation.

*   **Example Subscription Message (Client to Server)**:
    ```json
    {
      "action": "subscribe",
      "topic": "order_updates:ORDER_ID_123"
    }
    ```
    ```json
    {
      "action": "subscribe",
      "topic": "driver_location:ORDER_ID_123" // Or driver_location:DRIVER_ID_XYZ
    }
    ```

### 5.3. Handling Incoming Messages (Server to Client):

The client listens for messages from the server on subscribed topics.

*   **Order Status Update Example**:
    ```json
    {
      "topic": "order_updates:ORDER_ID_123",
      "data": {
        "order_id": "ORDER_ID_123",
        "status": "out_for_delivery",
        "estimated_delivery_time": "2025-06-09T22:45:00Z"
      }
    }
    ```
*   **Driver Location Update Example**:
    ```json
    {
      "topic": "driver_location:ORDER_ID_123",
      "data": {
        "order_id": "ORDER_ID_123", // or driver_id
        "latitude": 34.052235,
        "longitude": -118.243683,
        "timestamp": "2025-06-09T22:30:00Z"
      }
    }
    ```

### 5.4. Using Lat/Lon for WebSocket:

*   For driver tracking, the `latitude` and `longitude` values received via WebSocket are the core data.
*   The client application should:
    1.  Parse these coordinates.
    2.  Update the driver's position on a map interface.
    3.  Optionally, draw a polyline to show the driver's path if historical points are sent or stored.
    4.  Ensure smooth updates on the map to reflect movement.

## 6. API Interaction Best Practices

### 6.1. Base API URL:

*   All API requests should be prefixed with the base URL (e.g., `https://api.yourdomain.com/api/v1/`). This should be configurable in the client app.

### 6.2. Common Headers:

*   `Authorization: Bearer <FIREBASE_ID_TOKEN>`: For all authenticated requests.
*   `Content-Type: application/json`: For requests sending JSON data (e.g., POST, PUT).
*   `Accept: application/json`: To indicate the client expects a JSON response.

### 6.3. Error Handling:

*   The client should gracefully handle API error responses (e.g., 400, 401, 403, 404, 500).
*   Error responses from the API should ideally follow a consistent format:
    ```json
    {
      "detail": "Error message or specific error details object"
    }
    ```
*   For 401 (Unauthorized), the client should attempt to refresh the Firebase ID token or prompt the user to re-authenticate.

## 7. Important Considerations for Client App

### 7.1. UI/UX:

*   **Clear Order Flow**: Intuitive steps for placing and tracking orders.
*   **Real-time Feedback**: Visual cues for successful actions, loading states, and errors.
*   **Map Integration**: Smooth and accurate map display for driver tracking.

### 7.2. Push Notifications:

*   Integrate Firebase Cloud Messaging (FCM) or similar for push notifications about order status changes (e.g., "Order Confirmed", "Driver Assigned", "Delivered").
*   The backend would trigger these notifications based on events in `order_service.py`.

### 7.3. Offline Support:

*   Consider caching essential data (like recent orders) for viewing offline.
*   Queue actions (like order creation attempts) to be retried when connectivity is restored. This is an advanced feature.

### 7.4. Security:

*   **Token Management**: Securely store and handle Firebase ID tokens. Do not hardcode sensitive information.
*   **Input Validation**: Validate user input on the client-side before sending to the API (though server-side validation is paramount).
*   **HTTPS**: Ensure all API and WebSocket communications are over HTTPS/WSS.

### 7.5. Data Persistence:

*   Locally store user preferences, and potentially non-sensitive session data to improve user experience.

## 8. High-Level Client Workflow Summary

1.  **App Launch**:
    *   Initialize Firebase SDK.
    *   Check current Firebase auth state.
2.  **Authentication**:
    *   If not authenticated, show Login/Sign-Up screen.
    *   User authenticates via Firebase.
    *   Client obtains Firebase ID Token.
    *   Client may call a `/api/auth/me` endpoint with the token to get user profile details from the backend.
3.  **WebSocket Connection**:
    *   Establish WebSocket connection using the Firebase ID Token for authentication.
4.  **Placing an Order**:
    *   User navigates to "New Order" screen.
    *   Fills in order details (pickup, dropoff, items).
    *   Submits order (POST to `/api/client/orders/` with ID Token).
    *   On success, client receives `order_id`.
    *   Client subscribes to `order_updates:{order_id}` and potentially `driver_location:{order_id}` via WebSocket.
5.  **Tracking an Order**:
    *   User views "My Orders" screen (GET `/api/client/orders/`).
    *   Selects an active order.
    *   Client displays order status, updated in real-time via WebSocket messages on `order_updates:{order_id}`.
    *   If driver is assigned and en route, client displays driver's location on a map, updated via WebSocket messages on `driver_location:{order_id}`.
6.  **Receiving Updates**:
    *   Client app listens for WebSocket messages and updates UI accordingly (order status, driver location).
    *   Client app receives push notifications for key events.
7.  **Logout**:
    *   Client signs out via Firebase SDK.
    *   Clear local session data and ID token.
    *   Close WebSocket connection.

This guide provides a foundational understanding for building the client application. Specific endpoint paths, request/response schemas, and WebSocket topic names should be finalized based on the actual backend implementation (primarily in `app/api/`, `app/schemas/`, and `app/services/`).
