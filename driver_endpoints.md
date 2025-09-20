# Driver Endpoints Guide

This guide provides comprehensive documentation for all endpoints specifically designed for drivers in our system. These endpoints enable drivers to manage orders, update their profile, and handle location tracking.

## 1. Driver Registration
- **Endpoint**: `POST /auth/register`
- **Description**: Register a new driver account. This endpoint creates a user record with the driver role.
- **Request Body**: UserRegistration object
  - `firebase_uid`: str (Firebase user ID)
  - `user_type`: UserRole enum (Must be "driver")
- **Response**: UserResponse object
  - `id`: str (User ID)
  - `email`: Optional[EmailStr] (User's email)
  - `full_name`: Optional[str] (User's full name)
  - `phone_number`: Optional[str] (User's phone number)
  - `role`: str (User role, e.g., "driver")
  - `created_at`: datetime (User creation timestamp)
- **Requirements**: None
- **Example Request Body**:
```json
{
  "firebase_uid": "firebase-user-id-123",
  "user_type": "driver"
}
```
- **Example Response**:
```json
{
  "id": "firebase-user-id-123",
  "email": null,
  "full_name": null,
  "phone_number": null,
  "role": "driver",
  "created_at": "2025-08-16T10:00:00.000Z",
  "client_profile": null,
  "driver_profile": null
}
```

## 2. Create Driver Profile
- **Endpoint**: `POST /auth/driver-profile`
- **Description**: Create a driver profile for the current user. This endpoint is used after registration to set up the driver's specific information.
- **Request Body**: DriverCreate object
  - `license_no`: str (Driver's license number)
  - `vehicle_type`: str (Type of vehicle)
  - `email`: Optional[EmailStr] (Driver's email)
  - `full_name`: Optional[str] (Driver's full name)
  - `phone_number`: Optional[str] (Driver's phone number)
- **Response**: DriverResponse object
  - `driver_id`: string (Driver's ID)
  - `license_no`: str (Driver's license number)
  - `vehicle_type`: str (Type of vehicle)
  - `is_available`: bool (Current availability status)
  - `user`: UserResponse object
    - `id`: str (User ID)
    - `email`: Optional[EmailStr] (User's email)
    - `full_name`: Optional[str] (User's full name)
    - `phone_number`: Optional[str] (User's phone number)
    - `role`: str (User role, e.g., "driver")
- **Requirements**: User must be authenticated and have the driver role
- **Example Request Body**:
```json
{
  "license_no": "DL123456",
  "vehicle_type": "Car",
  "email": "driver@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890"
}
```
- **Example Response**:
```json
{
  "driver_id": "driver123",
  "license_no": "DL123456",
  "vehicle_type": "Car",
  "is_available": true,
  "user": {
    "id": "user123",
    "email": "driver@example.com",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "role": "driver",
    "created_at": "2025-08-16T10:00:00.000Z",
    "client_profile": null,
    "driver_profile": null
  }
}
```

## 3. Get Available Orders
- **Endpoint**: `GET /driver/available-orders`
- **Description**: Get all pending orders for drivers
- **Response**: List of OrderResponse objects
- **Requirements**: User must be a driver
- **Example Response**:
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "client_id": "client123",
    "driver_id": "driver789",
    "order_type": "delivery",
    "status": "pending",
    "pickup_address": "123 Main St, Anytown",
    "pickup_latitude": "34.0522",
    "pickup_longitude": "-118.2437",
    "dropoff_address": "456 Oak Ave, Anytown",
    "dropoff_latitude": "34.0600",
    "dropoff_longitude": "-118.2500",
    "price": null,
    "distance_km": null,
    "special_instructions": "Handle with care",
    "created_at": "2025-08-16T10:00:00.000Z"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef0",
    "client_id": "client456",
    "driver_id": "driver789",
    "order_type": "pickup",
    "status": "pending",
    "pickup_address": "789 Pine Ln, Anytown",
    "pickup_latitude": "34.0700",
    "pickup_longitude": "-118.2600",
    "dropoff_address": "101 Elm St, Anytown",
    "dropoff_latitude": "34.0800",
    "dropoff_longitude": "-118.2700",
    "price": null,
    "distance_km": null,
    "special_instructions": null,
    "created_at": "2025-08-16T10:15:00.000Z"
  }
]
```

## 4. Accept Order
- **Endpoint**: `POST /driver/accept-order/{order_id}`
- **Description**: Accept an order. **Note**: Order pricing is handled server-side during order creation and is not managed by the driver during acceptance.
- **Request Body**: OrderAccept object
  - `driver_id`: string (ID of the driver accepting the order)
  - `estimated_price`: Optional[Decimal] (Estimated price for the order, if provided)
- **Response**: OrderResponse object
- **Requirements**:
  - User must be a driver
  - Driver can only accept orders for themselves
- **Example Request Body**:
```json
{
  "driver_id": "driver789",
  "estimated_price": 15.50
}
```
- **Example Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "client_id": "client123",
  "driver_id": "driver789",
  "order_type": "delivery",
  "status": "accepted",
  "pickup_address": "123 Main St, Anytown",
  "pickup_latitude": "34.0522",
  "pickup_longitude": "-118.2437",
  "dropoff_address": "456 Oak Ave, Anytown",
  "dropoff_latitude": "34.0600",
  "dropoff_longitude": "-118.2500",
  "price": 15.50,
  "distance_km": 5.2,
  "special_instructions": "Handle with care",
  "created_at": "2025-08-16T10:00:00.000Z"
}
```

## 5. Get My Orders
- **Endpoint**: `GET /driver/my-orders`
- **Description**: Get all orders for current driver
- **Response**: List of OrderResponse objects
- **Requirements**: User must be a driver
- **Example Response**:
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "client_id": "client123",
    "driver_id": "driver789",
    "order_type": "delivery",
    "status": "accepted",
    "pickup_address": "123 Main St, Anytown",
    "pickup_latitude": "34.0522",
    "pickup_longitude": "-118.2437",
    "dropoff_address": "456 Oak Ave, Anytown",
    "dropoff_latitude": "34.0600",
    "dropoff_longitude": "-118.2500",
    "price": 15.50,
    "distance_km": 5.2,
    "special_instructions": "Handle with care",
    "created_at": "2025-08-16T10:00:00.000Z"
  },
  {
    "id": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
    "client_id": "client999",
    "driver_id": "driver789",
    "order_type": "pickup",
    "status": "in_transit",
    "pickup_address": "222 Baker St, Anytown",
    "pickup_latitude": "34.0900",
    "pickup_longitude": "-118.2800",
    "dropoff_address": "333 Cherry Ave, Anytown",
    "dropoff_latitude": "34.1000",
    "dropoff_longitude": "-118.2900",
    "price": 20.00,
    "distance_km": 8.1,
    "special_instructions": null,
    "created_at": "2025-08-16T11:30:00.000Z"
  }
]
```

## 6. Update Order Status
- **Endpoint**: `PUT /driver/orders/{order_id}/status`
- **Description**: Update order status
- **Request Body**: OrderStatusUpdate object
  - `status`: OrderStatus enum (New status for the order)
- **Response**: OrderResponse object
- **Requirements**:
  - User must be a driver
  - Driver must own the order
- **Example Request Body**:
```json
{
  "status": "completed"
}
```
- **Example Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "client_id": "client123",
  "driver_id": "driver789",
  "order_type": "delivery",
  "status": "completed",
  "pickup_address": "123 Main St, Anytown",
  "pickup_latitude": "34.0522",
  "pickup_longitude": "-118.2437",
  "dropoff_address": "456 Oak Ave, Anytown",
  "dropoff_latitude": "34.0600",
  "dropoff_longitude": "-118.2500",
  "price": 15.50,
  "distance_km": 5.2,
  "special_instructions": "Handle with care",
  "created_at": "2025-08-16T10:00:00.000Z"
}
```

## 7. Update Location
- **Endpoint**: `POST /driver/location`
- **Description**: Update driver location
- **Request Body**: DriverLocationUpdate object
  - `latitude`: float (Current latitude of the driver)
  - `longitude`: float (Current longitude of the driver)
- **Response**: Success message
- **Requirements**: User must be a driver
- **Example Request Body**:
```json
{
  "latitude": 34.0522,
  "longitude": -118.2437
}
```
- **Example Response**:
```json
{
  "message": "Location updated successfully"
}
```

## 8. Update Driver Profile
- **Endpoint**: `PUT /driver/profile`
- **Description**: Update current driver's profile
- **Request Body**: DriverProfileUpdate object
  - `email`: Optional[EmailStr] (Driver's email)
  - `full_name`: Optional[str] (Driver's full name)
  - `phone_number`: Optional[str] (Driver's phone number)
  - `license_no`: Optional[str] (Driver's license number)
  - `vehicle_type`: Optional[str] (Type of vehicle)
- **Response**: DriverProfileResponse object
  - `driver_id`: string (Driver's ID)
  - `license_no`: Optional[str] (Driver's license number)
  - `vehicle_type`: Optional[str] (Type of vehicle)
  - `is_available`: bool (Current availability status)
  - `user`: UserResponse object
    - `email`: Optional[EmailStr] (Driver's email)
    - `full_name`: Optional[str] (Driver's full name)
    - `phone_number`: Optional[str] (Driver's phone number)
- **Requirements**: User must be a driver
- **Example Request Body**:
```json
{
  "full_name": "Jane Doe",
  "phone_number": "+1234567890",
  "vehicle_type": "Motorcycle"
}
```
- **Example Response**:
```json
{
  "driver_id": "driver789",
  "license_no": "DL98765",
  "vehicle_type": "Motorcycle",
  "is_available": true,
  "user": {
    "id": "user123",
    "email": "jane.doe@example.com",
    "full_name": "Jane Doe",
    "phone_number": "+1234567890",
    "role": "driver",
    "created_at": "2025-01-01T12:00:00.000Z",
    "client_profile": null,
    "driver_profile": null
  }
}
```

## 9. Update Driver Availability
- **Endpoint**: `PUT /driver/profile/availability`
- **Description**: Update current driver's availability status
- **Request Body**: DriverAvailabilityUpdate object
  - `is_available`: bool (Availability status of the driver)
- **Response**: DriverProfileResponse object
  - `driver_id`: string (Driver's ID)
  - `license_no`: Optional[str] (Driver's license number)
  - `vehicle_type`: Optional[str] (Type of vehicle)
  - `is_available`: bool (Current availability status)
  - `user`: UserResponse object
    - `email`: Optional[EmailStr] (Driver's email)
    - `full_name`: Optional[str] (Driver's full name)
    - `phone_number`: Optional[str] (Driver's phone number)
- **Requirements**: User must be a driver
- **Example Request Body**:
```json
{
  "is_available": false
}
```
- **Example Response**:
```json
{
  "driver_id": "driver789",
  "license_no": "DL98765",
  "vehicle_type": "Motorcycle",
  "is_available": false,
  "user": {
    "id": "user123",
    "email": "jane.doe@example.com",
    "full_name": "Jane Doe",
    "phone_number": "+1234567890",
    "role": "driver",
    "created_at": "2025-01-01T12:00:00.000Z",
    "client_profile": null,
    "driver_profile": null
  }
}
```

# Driver WebSocket Guide

This section outlines the WebSocket communication for drivers, enabling real-time updates for location and order status.

## WebSocket Connection
- **Endpoint**: `ws://your-api-url/ws/{user_id}`
- **Description**: Establishes a WebSocket connection for a specific driver, identified by their `user_id`. This connection is used for sending and receiving real-time updates.
- **Requirements**: User must be authenticated as a driver.

## Message Types (Driver to Server)

### 1. Subscribe to Order Updates
- **Type**: `subscribe_order`
- **Description**: Drivers can subscribe to specific order updates to receive real-time notifications about changes to an order they are handling.
- **Payload**:
```json
{
  "type": "subscribe_order",
  "order_id": "the_order_id_to_subscribe_to"
}
```

### 2. Driver Location Update
- **Type**: `driver_location_update`
- **Description**: Drivers send their current location periodically to the server. This information can be used for real-time tracking by clients.
- **Payload**:
```json
{
  "type": "driver_location_update",
  "latitude": 34.0522,
  "longitude": -118.2437
}
```

### 3. Test Message
- **Type**: `test_message`
- **Description**: A simple message type for testing the WebSocket connection.
- **Payload**:
```json
{
  "type": "test_message",
  "content": "Hello from driver!"
}
```

## Message Types (Server to Driver)

### 1. Subscribed Confirmation
- **Type**: `subscribed`
- **Description**: Confirms that the driver has successfully subscribed to order updates for a given `order_id`.
- **Payload**:
```json
{
  "type": "subscribed",
  "order_id": "the_order_id_subscribed_to"
}
```

### 2. Order Status Update
- **Type**: `order_status_update`
- **Description**: Notifies the driver about changes in the status of an order they are subscribed to.
- **Payload**:
```json
{
  "type": "order_status_update",
  "order_id": "the_order_id",
  "status": "in_transit",
  "timestamp": "2025-08-16T12:45:00.000Z",
  "driver_location": {
    "driver_id": "driver789",
    "latitude": 34.0550,
    "longitude": -118.2450,
    "timestamp": "2025-08-16T12:44:55.000Z"
  }
}
```

### 3. Driver Location Broadcast (for other drivers/clients, if applicable)
- **Type**: `driver_location_update`
- **Description**: (Note: While drivers send their location, this message type is primarily for broadcasting to clients or other relevant parties. Drivers might receive this if they are tracking another driver, though the primary use case for drivers is sending their own location.)
- **Payload**:
```json
{
  "type": "driver_location_update",
  "driver_id": "another_driver_id",
  "latitude": 34.1000,
  "longitude": -118.3000,
  "timestamp": "2025-08-16T12:46:00.000Z"
}
```

### 4. Test Response
- **Type**: `test_response`
- **Description**: A response to a `test_message` sent by the driver.
- **Payload**:
```json
{
  "type": "test_response",
  "content": "Server received your test message: Hello from driver!"
}
