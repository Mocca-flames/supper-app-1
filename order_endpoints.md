### Order Endpoints Documentation for Client

Endpoints must be prefixed with `/api/`

#### Client Endpoints
1. **POST /client/orders/estimate**
   - Calculate and return the estimated price and distance for a potential order based on location and service details, without creating an order record
   - Headers: `Authorization` (Bearer token)
   - Request Body: `OrderEstimateRequest`
     - service_type: "rideshare | medical_transport | food_delivery | product_delivery"
     - pickup_latitude: number
     - pickup_longitude: number
     - dropoff_latitude: number
     - dropoff_longitude: number
     - passenger_count: number (optional, for rideshare)
     - vehicle_type: string (optional, for rideshare)
     - mobility_needs: string[] (optional, for medical_transport)
     - transport_type: string (optional, for medical_transport)
     - package_size: string (optional, for delivery)
     - delivery_time_preference: string (optional, for delivery)
   - Response: `CostEstimationResponse`
   - **Note**: This endpoint requires an Authorization header with a valid Firebase token.
     - Example: `Authorization: Bearer <your_firebase_token>`


2. **POST /client/orders**
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

3. **GET /client/orders**
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

4. **GET /client/orders/{order_id}**
   - Get specific order details
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

5. **POST /orders/{order_id}/track**
   - Start tracking an order
   - Path Parameters: `order_id`
   - Response: `TrackingSessionResponse`
     - session_id: str
     - order_id: str
     - status: str
     - message: Optional[str] = None

6. **PATCH /orders/{order_id}/cancel**
   - Cancel a specific order
   - Path Parameters: `order_id`
   - Response: `OrderResponse`

7. **GET /orders/{order_id}/location**
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

4. **CostEstimationResponse**
   - Schema for order estimation response
   - Fields:
     - estimate: object
       - base_fare: float
       - distance_fare: float
       - service_fee: float
       - total: float
       - estimated_duration_minutes: int
       - currency: str
       - surge_multiplier: float
       - medical_surcharge: float
       - package_surcharge: float
       - delivery_fee: float
     - valid_until: str (ISO 8601 datetime)

5. **OrderEstimateRequest**
   - Schema for order estimation request
   - Fields:
     - service_type: str
     - pickup_latitude: float
     - pickup_longitude: float
     - dropoff_latitude: float
     - dropoff_longitude: float
     - passenger_count: Optional[int] = None
     - vehicle_type: Optional[str] = None
     - mobility_needs: Optional[List[str]] = None
     - transport_type: Optional[str] = None
     - package_size: Optional[str] = None
     - delivery_time_preference: Optional[str] = None

### Authentication

To access the order endpoints, you need to include an Authorization header with a valid Firebase token in your requests. The token should be obtained from Firebase Authentication and included in the header as follows:

- **Authorization**: `Bearer <your_firebase_token>`

Ensure that the token is valid and not expired. The server will verify the token and retrieve the user information based on the token.
