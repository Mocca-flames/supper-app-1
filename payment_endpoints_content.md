### 2.16 Create Refund

- **Endpoint:** `POST /payments/refund`
- **Method:** `POST`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "payment_id": "string",
  "order_id": "string",
  "amount": "decimal",
  "reason": "string"
}
```
- **Response (200 OK):**
```json
{
  "id": "string",
  "payment_id": "string",
  "order_id": "string",
  "amount": "decimal",
  "reason": "string",
  "status": "pending",
  "processed_at": "string",
  "created_at": "2025-08-11T08:45:49.071Z",
  "updated_at": "2025-08-11T08:45:49.071Z"
}
```

### 2.17 Get Order Payments

- **Endpoint:** `GET /payments/order/{order_id}`
- **Method:** `GET`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
[
  {
    "id": "string",
    "order_id": "string",
    "user_id": "string",
    "payment_type": "client_payment",
    "amount": "decimal",
    "currency": "ZAR",
    "payment_method": "credit_card",
    "status": "completed",
    "transaction_id": "string",
    "created_at": "2025-08-11T08:45:49.071Z",
    "updated_at": "2025-08-11T08:45:49.071Z"
  }
]
```

### 2.18 Get User Payments

- **Endpoint:** `GET /payments/user/{user_id}`
- **Method:** `GET`
- **Path Parameters:**
  - `user_id` (string, required) — ID of the user
- **Query Parameters:**
  - `payment_type` (string, optional) — Filter by payment type (client_payment, driver_payment)
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
[
  {
    "id": "string",
    "order_id": "string",
    "user_id": "string",
    "payment_type": "client_payment",
    "amount": "decimal",
    "currency": "ZAR",
    "payment_method": "credit_card",
    "status": "completed",
    "transaction_id": "string",
    "created_at": "2025-08-11T08:45:49.071Z",
    "updated_at": "2025-08-11T08:45:49.071Z"
  }
]
```

### 2.19 Get Order Refunds

- **Endpoint:** `GET /payments/refunds/order/{order_id}`
- **Method:** `GET`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
[
  {
    "id": "string",
    "payment_id": "string",
    "order_id": "string",
    "amount": "decimal",
    "reason": "string",
    "status": "completed",
    "processed_at": "string",
    "created_at": "2025-08-11T08:45:49.071Z",
    "updated_at": "2025-08-11T08:45:49.071Z"
  }
]