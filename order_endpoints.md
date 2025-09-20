### Order Endpoints Documentation for Client

Endpoints must be prefixed with `/api/`

#### Client Endpoints

1. **POST /client/orders**
   - Create a new order/ride request
   - Request Body: `OrderCreate`
     - order_type: OrderType
     - pickup_address: str
     - pickup_latitude: str
     - pickup_longitude: str
     - dropoff_address: str
     - dropoff_latitude: str
     - dropoff_longitude: str
     - client_id: str
     - distance_km: str
     - special_instructions: Optional[str] = None
     - patient_details: Optional[str] = None
     - medical_items: Optional[str] = None
   - Response: `OrderResponse`
   - **Note**: This endpoint requires an Authorization header with a valid Firebase token.
     - Example: `Authorization: Bearer <your_firebase_token>`

2. **GET /client/orders**
   - Get all orders for the current client
   - Response: List of `OrderResponse`
     - id: str
     - client_id: str
     - driver_id: Optional[str] = None
     - order_type: OrderType
     - status: OrderStatus
     - pickup_address: str
     - pickup_latitude: Optional[str] = None
     - pickup_longitude: Optional[str] = None
     - dropoff_address: str
     - dropoff_latitude: Optional[str] = None
     - dropoff_longitude: Optional[str] = None
     - price: Optional[Decimal] = None
     - distance_km: Optional[Decimal] = None
     - special_instructions: Optional[str] = None
     - created_at: datetime

3. **GET /client/orders/{order_id}**
   - Get specific order details
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

4. **POST /orders/{order_id}/track**
   - Start tracking an order
   - Path Parameters: `order_id`
   - Response: `TrackingSessionResponse`
     - session_id: str
     - order_id: str
     - status: str
     - message: Optional[str] = None

5. **PATCH /orders/{order_id}/cancel**
   - Cancel a specific order
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

6. **GET /orders/{order_id}/location**
   - Get driver location for an order
   - Path Parameters: `order_id`
   - Response: `DriverLocationResponse`
     - driver_id: str
     - latitude: float
     - longitude: float
     - timestamp: datetime

### Order Schemas

1. **OrderCreate**
   - Schema for creating an order as a client
   - Fields:
     - order_type: OrderType
     - pickup_address: str
     - pickup_latitude: str
     - pickup_longitude: str
     - dropoff_address: str
     - dropoff_latitude: str
     - dropoff_longitude: str
     - client_id: str
     - distance_km: str
     - special_instructions: Optional[str] = None
     - patient_details: Optional[str] = None
     - medical_items: Optional[str] = None

2. **OrderResponse**
   - Schema for order response
   - Fields:
     - id: str
     - client_id: str
     - driver_id: Optional[str] = None
     - order_type: OrderType
     - status: OrderStatus
     - pickup_address: str
     - pickup_latitude: Optional[str] = None
     - pickup_longitude: Optional[str] = None
     - dropoff_address: str
     - dropoff_latitude: Optional[str] = None
     - dropoff_longitude: Optional[str] = None
     - price: Optional[Decimal] = None
     - distance_km: Optional[Decimal] = None
     - special_instructions: Optional[str] = None
     - created_at: datetime

3. **TrackingSessionResponse**
   - Schema for tracking session response
   - Fields:
     - session_id: str
     - order_id: str
     - status: str
     - message: Optional[str] = None

### Authentication

To access the order endpoints, you need to include an Authorization header with a valid Firebase token in your requests. The token should be obtained from Firebase Authentication and included in the header as follows:

- **Authorization**: `Bearer <your_firebase_token>`

Ensure that the token is valid and not expired. The server will verify the token and retrieve the user information based on the token.
