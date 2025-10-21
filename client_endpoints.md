# Client Endpoints

## User Profile

### Get User Profile

**GET** `/api/user/profile`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `UserResponse` JSON

```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "phone_number": "string",
  "role": "client",
  "created_at": "2023-10-27T10:00:00Z",
  "client_profile": {
    "client_id": "string",
    "home_address": "string",
    "is_verified": true
  },
  "driver_profile": null
}
```

### Update User Profile

**PUT** `/api/user/profile`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "email": "string",
  "full_name": "string",
  "phone_number": "string"
}
```

- **Response**: `200 OK` with updated `UserResponse` JSON

```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "phone_number": "string",
  "role": "client",
  "created_at": "2023-10-27T10:00:00Z",
  "client_profile": {
    "client_id": "string",
    "home_address": "string",
    "is_verified": true
  },
  "driver_profile": null
}
```

## Client Orders

### Create Order

**POST** `/api/client/orders`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "order_type": "ride",
  "pickup_address": "string",
  "pickup_latitude": "number",
  "pickup_longitude": "number",
  "dropoff_address": "string",
  "dropoff_latitude": "number",
  "dropoff_longitude": "number",
  "distance_km": "number",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string"
}
```

- **Response**: `200 OK` with `OrderResponse` JSON

```json
{
  "id": "string",
  "client_id": "string",
  "driver_id": "string",
  "order_type": "ride",
  "status": "pending",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "price": 0.0,
  "distance_km": 0.0,
  "special_instructions": "string",
  "created_at": "2023-10-27T10:00:00Z",
  "payment_status": "pending",
  "total_paid": 0.0,
  "total_refunded": 0.0
}
```

### Get My Orders

**GET** `/api/client/orders`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with array of `OrderResponse` JSON

```json
[
  {
    "id": "string",
    "client_id": "string",
    "driver_id": "string",
    "order_type": "ride",
    "status": "pending",
    "pickup_address": "string",
    "pickup_latitude": "string",
    "pickup_longitude": "string",
    "dropoff_address": "string",
    "dropoff_latitude": "string",
    "dropoff_longitude": "string",
    "price": 0.0,
    "distance_km": 0.0,
    "special_instructions": "string",
    "created_at": "2023-10-27T10:00:00Z",
    "payment_status": "pending",
    "total_paid": 0.0,
    "total_refunded": 0.0
  }
]
```

### Get Order Details

**GET** `/api/client/orders/{order_id}`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `OrderResponse` JSON

```json
{
  "id": "string",
  "client_id": "string",
  "driver_id": "string",
  "order_type": "ride",
  "status": "pending",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "price": 0.0,
  "distance_km": 0.0,
  "special_instructions": "string",
  "created_at": "2023-10-27T10:00:00Z",
  "payment_status": "pending",
  "total_paid": 0.0,
  "total_refunded": 0.0
}
```

### Update Order

**PUT** `/api/client/orders/{order_id}`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "pickup_address": "string",
  "pickup_latitude": "number",
  "pickup_longitude": "number",
  "dropoff_address": "string",
  "dropoff_latitude": "number",
  "dropoff_longitude": "number",
  "special_instructions": "string"
}
```

- **Response**: `200 OK` with updated `OrderResponse` JSON

```json
{
  "id": "string",
  "client_id": "string",
  "driver_id": "string",
  "order_type": "ride",
  "status": "pending",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "price": 0.0,
  "distance_km": 0.0,
  "special_instructions": "string",
  "created_at": "2023-10-27T10:00:00Z",
  "payment_status": "pending",
  "total_paid": 0.0,
  "total_refunded": 0.0
}
```

## Driver Location

### Get Driver Location

**GET** `/api/client/driver/{driver_id}/location`

- **Path**: `driver_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `DriverLocationResponse` JSON

```json
{
  "driver_id": "string",
  "latitude": 0.0,
  "longitude": 0.0
}
```

## Client Profile

### Update Client Profile

**PUT** `/api/client/profile`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "home_address": "string"
}
```

- **Response**: `200 OK` with `ClientResponse` JSON

```json
{
  "client_id": "string",
  "home_address": "string",
  "is_verified": true
}
```

## Order Tracking and Management

### Track Order

**POST** `/api/orders/{order_id}/track`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `TrackingSessionResponse` JSON

```json
{
  "session_id": "string",
  "order_id": "string",
  "status": "active",
  "message": "string"
}
```

### Cancel Order

**PATCH** `/api/orders/{order_id}/cancel`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `OrderResponse` JSON

```json
{
  "id": "string",
  "client_id": "string",
  "driver_id": "string",
  "order_type": "ride",
  "status": "cancelled",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "price": 0.0,
  "distance_km": 0.0,
  "special_instructions": "string",
  "created_at": "2023-10-27T10:00:00Z",
  "payment_status": "pending",
  "total_paid": 0.0,
  "total_refunded": 0.0
}
```

### Get Order Driver Location

**GET** `/api/orders/{order_id}/location`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `DriverLocationResponse` or `null` JSON

```json
{
  "driver_id": "string",
  "latitude": 0.0,
  "longitude": 0.0
}
```

## Payments

### Create Payment

**POST** `/api/payments/create`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "order_id": "string",
  "user_id": "string",
  "payment_type": "client_payment",
  "amount": "number",
  "currency": "ZAR",
  "payment_method": "credit_card",
  "transaction_id": "string",
  "transaction_details": {}
}
```

- **Response**: `200 OK` with `PaymentResponse` JSON

```json
{
  "id": "string",
  "order_id": "string",
  "user_id": "string",
  "payment_type": "client_payment",
  "amount": 0.0,
  "currency": "ZAR",
  "payment_method": "credit_card",
  "status": "pending",
  "transaction_id": "string",
  "created_at": "2023-10-27T10:00:00Z",
  "updated_at": "2023-10-27T10:00:00Z"
}
```

### Get Order Payments

**GET** `/api/payments/order/{order_id}`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with array of `PaymentResponse` JSON

```json
[
  {
    "id": "string",
    "order_id": "string",
    "user_id": "string",
    "payment_type": "client_payment",
    "amount": 0.0,
    "currency": "ZAR",
    "payment_method": "credit_card",
    "status": "pending",
    "transaction_id": "string",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z"
  }
]
```

### Get User Payments

**GET** `/api/payments/user/{user_id}`

- **Path**: `user_id` (string, required)
- **Query**: `payment_type` (optional, e.g., "client_payment")
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with array of `PaymentResponse` JSON

```json
[
  {
    "id": "string",
    "order_id": "string",
    "user_id": "string",
    "payment_type": "client_payment",
    "amount": 0.0,
    "currency": "ZAR",
    "payment_method": "credit_card",
    "status": "pending",
    "transaction_id": "string",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z"
  }
]
```

### Get Order Refunds

**GET** `/api/payments/refunds/order/{order_id}`

- **Path**: `order_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with array of `RefundResponse` JSON

```json
[
  {
    "id": "string",
    "payment_id": "string",
    "order_id": "string",
    "amount": 0.0,
    "reason": "string",
    "status": "pending",
    "processed_at": "2023-10-27T10:00:00Z",
    "created_at": "2023-10-27T10:00:00Z",
    "updated_at": "2023-10-27T10:00:00Z"
  }
]
```

### Query Payfast Transaction

**GET** `/api/payments/query/{pf_payment_id}`

- **Path**: `pf_payment_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with transaction status JSON

```json
{
  "status": "string",
  "message": "string",
  "data": {}
}
```

### Initialize Paystack Payment

**POST** `/api/payments/paystack/initialize`

- **Headers**: `Authorization` (Bearer token)
- **Description**: Initiates a Paystack transaction, creates a PENDING payment record, and returns the authorization URL for client redirection.
- **Request Body**: Same as `Create Payment` but with `"gateway": "paystack"`.
- **Response**: `200 OK` with custom response containing payment details and redirect URL.

```json
{
  "payment": {
    "id": "string",
    "order_id": "string",
    "status": "pending",
    "amount": 0.0
  },
  "access_code": "string",
  "authorization_url": "https://checkout.paystack.com/..."
}
```

### Verify Paystack Payment

**GET** `/api/payments/paystack/verify/{reference}`

- **Path**: `reference` (string, required - corresponds to the payment ID)
- **Headers**: `Authorization` (Bearer token)
- **Description**: Manually verifies a Paystack payment status using the transaction reference (payment ID). Used as a fallback after client redirection.
- **Response**: `200 OK` with verification status and updated payment details.

```json
{
  "status": "verified",
  "payment": {
    "id": "string",
    "status": "completed",
    "transaction_id": "string"
  }
}
```

## Driver Ratings

### Submit Driver Rating

**POST** `/api/ratings/drivers`

- **Headers**: `Authorization` (Bearer token)
- **Description**: Allows a client to submit a 5-star rating for a driver after a completed order.
- **Request Body**:

```json
{
  "driver_id": "string",
  "order_id": "string",
  "rating": 5
}
```

- **Response**: `201 Created` with `DriverRatingResponse` JSON

```json
{
  "id": "uuid",
  "driver_id": "string",
  "order_id": "string",
  "rating": 5,
  "client_id": "string",
  "created_at": "2023-10-27T10:00:00Z"
}
```

### Get Driver Average Rating

**GET** `/api/ratings/drivers/{driver_id}/average`

- **Path**: `driver_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Description**: Retrieves the average rating and total count for a specific driver.
- **Response**: `200 OK` with `DriverAverageRating` JSON

```json
{
  "driver_id": "string",
  "average_rating": 4.5,
  "total_ratings": 10
}
```

## Authentication and Registration

### Register User

**POST** `/api/auth/register`

- **Request Body**: JSON object with required fields:
  - `firebase_uid` (string, required)
  - `user_type` (string, required, e.g., `"client"` or `"driver"`)
- **Example Request Body**:

```json
{
  "firebase_uid": "rFbbyZGZ0zgxnpoosw219ONNrXt2",
  "user_type": "client"
}
```

- **Response**: `200 OK` with `UserResponse` JSON

### Important Notes on /api/auth/register

- This endpoint requires a POST request with parameters sent in the JSON body.
- Sending `firebase_uid` and `user_type` as query parameters will result in errors such as:
  - `422 Unprocessable Entity` indicating missing fields in the query parameters.
  - Or a `404 Not Found` error.
- Ensure your client sends the data in the request body as JSON, not as query parameters.
- This endpoint does not require an `Authorization` header.

### Example curl Request

```bash
curl -X POST https://your-api-domain.com/api/auth/register \
-H "Content-Type: application/json" \
-d '{"firebase_uid": "rFbbyZGZ0zgxnpoosw219ONNrXt2", "user_type": "client"}'
```

### Create Client Profile

**POST** `/api/auth/client-profile`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "home_address": "string"
}
```

- **Response**: `200 OK` with `ClientResponse` JSON

```json
{
  "client_id": "string",
  "home_address": "string",
  "is_verified": true
}
```

### Get Current User Info

**GET** `/api/auth/me`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `UserResponse` JSON

```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "phone_number": "string",
  "role": "client",
  "created_at": "2023-10-27T10:00:00Z",
  "client_profile": {
    "client_id": "string",
    "home_address": "string",
    "is_verified": true
  },
  "driver_profile": null
}
```

## Order Deletion (Admin function, but affects clients)

### Delete All Client Orders

**DELETE** `/api/orders/delete_all`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK`

```json
{
  "message": "All orders deleted successfully"
}
```

## Driver Ratings

### Submit Driver Rating

**POST** `/api/ratings/drivers`

- **Headers**: `Authorization` (Bearer token)
- **Description**: Allows a client to submit a 5-star rating for a driver after a completed order.
- **Request Body**:

```json
{
  "driver_id": "string",
  "order_id": "string",
  "rating": 5
}
```

- **Response**: `201 Created` with `DriverRatingResponse` JSON

```json
{
  "id": "uuid",
  "driver_id": "string",
  "order_id": "string",
  "rating": 5,
  "client_id": "string",
  "created_at": "2023-10-27T10:00:00Z"
}
```

### Get Driver Average Rating

**GET** `/api/ratings/drivers/{driver_id}/average`

- **Path**: `driver_id` (string, required)
- **Headers**: `Authorization` (Bearer token)
- **Description**: Retrieves the average rating and total count for a specific driver.
- **Response**: `200 OK` with `DriverAverageRating` JSON

```json
{
  "driver_id": "string",
  "average_rating": 4.5,
  "total_ratings": 10
}
```

## Authentication and Registration

### Register User

**POST** `/api/auth/register`

- **Request Body**: JSON object with required fields:
  - `firebase_uid` (string, required)
  - `user_type` (string, required, e.g., `"client"` or `"driver"`)
- **Example Request Body**:

```json
{
  "firebase_uid": "rFbbyZGZ0zgxnpoosw219ONNrXt2",
  "user_type": "client"
}
```

- **Response**: `200 OK` with `UserResponse` JSON

### Important Notes on /api/auth/register

- This endpoint requires a POST request with parameters sent in the JSON body.
- Sending `firebase_uid` and `user_type` as query parameters will result in errors such as:
  - `422 Unprocessable Entity` indicating missing fields in the query parameters.
  - Or a `404 Not Found` error.
- Ensure your client sends the data in the request body as JSON, not as query parameters.
- This endpoint does not require an `Authorization` header.

### Example curl Request

```bash
curl -X POST https://your-api-domain.com/api/auth/register \
-H "Content-Type: application/json" \
-d '{"firebase_uid": "rFbbyZGZ0zgxnpoosw219ONNrXt2", "user_type": "client"}'
```

### Create Client Profile

**POST** `/api/auth/client-profile`

- **Headers**: `Authorization` (Bearer token)
- **Request Body**:

```json
{
  "home_address": "string"
}
```

- **Response**: `200 OK` with `ClientResponse` JSON

```json
{
  "client_id": "string",
  "home_address": "string",
  "is_verified": true
}
```

### Get Current User Info

**GET** `/api/auth/me`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK` with `UserResponse` JSON

```json
{
  "id": "string",
  "email": "string",
  "full_name": "string",
  "phone_number": "string",
  "role": "client",
  "created_at": "2023-10-27T10:00:00Z",
  "client_profile": {
    "client_id": "string",
    "home_address": "string",
    "is_verified": true
  },
  "driver_profile": null
}
```

## Order Deletion (Admin function, but affects clients)

### Delete All Client Orders

**DELETE** `/api/orders/delete_all`

- **Headers**: `Authorization` (Bearer token)
- **Response**: `200 OK`

```json
{
  "message": "All orders deleted successfully"
}
```
