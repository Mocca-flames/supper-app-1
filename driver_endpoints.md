# Driver Endpoints

## 1. Get Available Orders
- **Endpoint**: `GET /driver/available-orders`
- **Description**: Get all pending orders for drivers
- **Response**: List of OrderResponse objects
- **Requirements**: User must be a driver

## 2. Accept Order
- **Endpoint**: `POST /driver/accept-order/{order_id}`
- **Description**: Accept an order. **Note**: Order pricing is handled server-side during order creation and is not managed by the driver during acceptance.
- **Request Body**: OrderAccept object
  - `driver_id`: string (ID of the driver accepting the order)
- **Response**: OrderResponse object
- **Requirements**:
  - User must be a driver
  - Driver can only accept orders for themselves

## 3. Get My Orders
- **Endpoint**: `GET /driver/my-orders`
- **Description**: Get all orders for current driver
- **Response**: List of OrderResponse objects
- **Requirements**: User must be a driver

## 4. Update Order Status
- **Endpoint**: `PUT /driver/orders/{order_id}/status`
- **Description**: Update order status
- **Request Body**: OrderStatusUpdate object
  - `status`: OrderStatus enum (New status for the order)
- **Response**: OrderResponse object
- **Requirements**:
  - User must be a driver
  - Driver must own the order

## 5. Update Location
- **Endpoint**: `POST /driver/location`
- **Description**: Update driver location
- **Request Body**: DriverLocationUpdate object
  - `latitude`: float (Current latitude of the driver)
  - `longitude`: float (Current longitude of the driver)
- **Response**: Success message
- **Requirements**: User must be a driver

## 6. Update Driver Profile
- **Endpoint**: `PUT /driver/profile`
- **Description**: Update current driver's profile
- **Request Body**: DriverProfileUpdate object
  - `email`: Optional[EmailStr] (Driver's email)
  - `full_name`: Optional[str] (Driver's full name)
  - `phone_number`: Optional[str] (Driver's phone number)
  - `license_no`: Optional[str] (Driver's license number)
  - `vehicle_type`: Optional[str] (Type of vehicle)
- **Response**: DriverProfileResponse object
- **Requirements**: User must be a driver

## 7. Update Driver Availability
- **Endpoint**: `PUT /driver/profile/availability`
- **Description**: Update current driver's availability status
- **Request Body**: DriverAvailabilityUpdate object
  - `is_available`: bool (Availability status of the driver)
- **Response**: DriverProfileResponse object
- **Requirements**: User must be a driver

# Authentication Endpoints

## 1. Register User
- **Endpoint**: `POST /auth/register`
- **Description**: Register a new user from Firebase UID, specifying their type (client or driver). **Note**: If the user type is 'driver', a driver profile must also be created using the `/auth/driver-profile` endpoint.
- **Request Body**:
  - `firebase_uid`: string (Firebase user ID)
  - `user_type`: UserRole enum ("client" or "driver")
- **Response**: UserResponse object

## 2. Create Client Profile
- **Endpoint**: `POST /auth/client-profile`
- **Description**: Create client profile for current user
- **Request Body**: ClientCreate object
  - `home_address`: Optional[str] (Client's home address)
- **Response**: ClientResponse object
- **Requirements**: User must not already have a client profile

## 3. Create Driver Profile
- **Endpoint**: `POST /auth/driver-profile`
- **Description**: Create driver profile for current user. This action creates the necessary `Driver` entry in the database, linking it to the user.
- **Request Body**: DriverCreate object
  - `license_no`: Optional[str] (Driver's license number)
  - `vehicle_type`: Optional[str] (Type of vehicle)
- **Response**: DriverResponse object
- **Requirements**: User must not already have a driver profile

## 4. Get Current User Info
- **Endpoint**: `GET /auth/me`
- **Description**: Get current user information
- **Response**: UserResponse object

## 5. Update User Profile
- **Endpoint**: `PUT /auth/profile`
- **Description**: Update current user's general profile information
- **Request Body**: UserProfileUpdate object
  - `email`: Optional[EmailStr] (User's email)
  - `full_name`: Optional[str] (User's full name)
  - `phone_number`: Optional[str] (User's phone number)
- **Response**: UserResponse object
