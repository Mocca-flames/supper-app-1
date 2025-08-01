### Order Endpoints Documentation for Client

#### Client Endpoints

1. **GET /orders**
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
   - **Note**: This endpoint requires an Authorization header with a valid Firebase token.
     - Example: `Authorization: Bearer <your_firebase_token>`

2. **POST /orders**
   - Create a new order/ride request
   - Request Body: `OrderCreate`
     - order_type: OrderType
     - pickup_address: str
     - pickup_latitude: str
     - pickup_longitude: str
     - dropoff_address: str
     - dropoff_latitude: str
     - dropoff_longitude: str
     - special_instructions: Optional[str] = None
   - Response: `OrderResponse`

3. **GET /orders/{order_id}/route**
   - Get specific order route details
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

4. **POST /orders/{order_id}/recalculate-route**
   - Recalculate order route
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

5. **POST /orders/{order_id}/track**
   - Start tracking an order
   - Path Parameters: `order_id`
   - Response: `TrackingSessionResponse`

6. **PATCH /orders/{order_id}/cancel**
   - Cancel a specific order
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

7. **GET /orders/{order_id}/location**
   - Get driver location for an order
   - Path Parameters: `order_id`
   - Response: `DriverLocationResponse`

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
     - special_instructions: Optional[str] = None

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
     - tracking_url: str

4. **DriverLocationResponse**
   - Schema for driver location response
   - Fields:
     - driver_id: str
     - latitude: float
     - longitude: float
     - timestamp: datetime

### Authentication

To access the order endpoints, you need to include an Authorization header with a valid Firebase token in your requests. The token should be obtained from Firebase Authentication and included in the header as follows:

- **Authorization**: `Bearer <your_firebase_token>`

Ensure that the token is valid and not expired. The server will verify the token and retrieve the user information based on the token.
