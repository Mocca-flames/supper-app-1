# Admin Panel API Guide

This guide documents the Admin API endpoints. All admin endpoints require an `admin_key` query parameter for authentication and use `/admin` as the base prefix.

**Admin Key:** `admin_secret_key_123`

---

## 1. Authentication

**Requirement:**
- `admin_key` (string, required) — Secret key for admin access
- All admin requests must include `?admin_key=Maurice@12!`
- Base URL prefix: `/api`

---

## 2. API Endpoints

### 2.1 Get All Clients

- **Endpoint:** `GET /admin/clients`
- **Method:** `GET`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
[
  {
    "client_id": "string",
    "full_name": "string",
    "email": "string",
    "phone_number": "string",
    "home_address": "string",
    "created_at": "string",
    "is_active": true
  }
]
```

### 2.2 Get All Drivers

- **Endpoint:** `GET /admin/drivers`
- **Method:** `GET`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
[
  {
    "driver_id": "string",
    "email": "string",
    "full_name": "string",
    "license_no": "string",
    "vehicle_type": "string",
    "is_available": true
  }
]
```

### 2.3 Get All Orders

- **Endpoint:** `GET /admin/orders`
- **Method:** `GET`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK)::**
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
    "price": "string",
    "distance_km": "string",
    "special_instructions": "string",
    "patient_details": "string",
    "medical_items": "string",
    "created_at": "2025-08-11T08:45:49.071Z"
  }
]
```

### 2.4 Create Order

- **Endpoint:** `POST /admin/orders`
- **Method:** `POST`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "order_type": "ride",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "client_id": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string"
}
```
- **Response (201 Created):**
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
  "price": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string",
  "created_at": "2025-08-11T08:48:03.183Z"
}
```

### 2.5 Delete Order

- **Endpoint:** `DELETE /admin/orders/{order_id}`
- **Method:** `DELETE`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order to delete
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "message": "Order successfully deleted",
  "deleted_order": {
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
    "price": "string",
    "distance_km": "string",
    "special_instructions": "string",
    "created_at": "2025-08-11T08:48:03.195Z"
  }
}
```

### 2.6 Calculate Price Preview

- **Endpoint:** `POST /admin/pricing/calculate`
- **Method:** `POST`
- **Query Parameters:**
  - `distance_km` (decimal, required) — Distance in kilometers
  - `rate_per_km` (decimal, optional) — Custom rate per km
  - `minimum_fare` (decimal, optional) — Custom minimum fare
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "distance_km": 10.5,
  "rate_per_km": 10.0,
  "minimum_fare": 50.0,
  "calculated_price": 105.0,
  "final_price": 105.0,
  "minimum_fare_applied": false
}
```

### 2.7 Override Order Price

- **Endpoint:** `PATCH /admin/orders/{order_id}/price`
- **Method:** `PATCH`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order to update
- **Query Parameters:**
  - `new_price` (decimal, required) — New price for the order
  - `reason` (string, optional) — Reason for price override
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
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
  "price": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string",
  "created_at": "2025-08-11T08:48:03.183Z"
}
```

### 2.8 Update Order Status

- **Endpoint:** `PATCH /admin/orders/{order_id}/status`
- **Method:** `PATCH`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order to update
- **Query Parameters:**
  - `new_status` (string, required) — New status for the order
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "message": "Order status updated successfully"
}
```

### 2.9 Search Orders

- **Endpoint:** `GET /admin/orders/search`
- **Method:** `GET`
- **Query Parameters:**
  - `client_email` (string, optional) — Search by client email
  - `status` (string, optional) — Filter by order status
  - `min_price` (decimal, optional) — Minimum price filter
  - `max_price` (decimal, optional) — Maximum price filter
  - `limit` (integer, optional) — Number of results to return (default: 50, max: 500)
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "total_found": 10,
  "orders": [
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
      "price": "string",
      "distance_km": "string",
      "special_instructions": "string",
      "patient_details": "string",
      "medical_items": "string",
      "created_at": "2025-08-11T08:45:49.071Z"
    }
  ]
}
```

### 2.10 Get Admin Stats Summary

- **Endpoint:** `GET /admin/stats/summary`
- **Method:** `GET`
- **Query Parameters:**
  - `days` (integer, optional) — Number of days to analyze (default: 30, max: 365)
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "period_days": 30,
  "period_start": "2025-07-13",
  "period_end": "2025-08-12",
  "total_orders": 120,
  "orders_by_status": {
    "pending": 10,
    "accepted": 20,
    "in_progress": 30,
    "completed": 50,
    "cancelled": 10
  },
  "total_revenue": 5000.0,
  "average_price": 41.67,
  "active_drivers": 15,
  "top_clients": [
    {
      "client_id": "client_123",
      "orders": 12
    }
  ]
}
```

### 2.11 Toggle Driver Availability

- **Endpoint:** `POST /admin/drivers/{driver_id}/toggle-availability`
- **Method:** `POST`
- **Path Parameters:**
  - `driver_id` (string, required) — ID of the driver
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "message": "Driver availability toggled",
  "driver_id": "string",
  "is_available": true
}
```

### 2.12 Apply Pricing Preset

- **Endpoint:** `POST /admin/pricing/preset/{preset}`
- **Method:** `POST`
- **Path Parameters:**
  - `preset` (string, required) — Pricing preset: rush_hour, off_peak, weekend, standard
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "preset_applied": "rush_hour",
  "rate_per_km": 15.0,
  "minimum_fare": 70.0,
  "message": "Applied rush_hour pricing preset"
}
```

### 2.13 Get Pricing Presets

- **Endpoint:** `GET /admin/pricing/presets`
- **Method:** `GET`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "presets": {
    "rush_hour": {
      "rate_per_km": "15.00",
      "minimum_fare": "70.00",
      "description": "Peak hours pricing"
    },
    "off_peak": {
      "rate_per_km": "8.00",
      "minimum_fare": "40.00",
      "description": "Off-peak discount pricing"
    },
    "weekend": {
      "rate_per_km": "12.00",
      "minimum_fare": "60.00",
      "description": "Weekend standard pricing"
    },
    "standard": {
      "rate_per_km": "10.00",
      "minimum_fare": "50.00",
      "description": "Default pricing"
    }
  }
}
```

### 2.14 Create Order with Custom Price

- **Endpoint:** `POST /admin/orders/create-with-custom-price`
- **Method:** `POST`
- **Query Parameters:**
  - `custom_price` (decimal, optional) — Override calculated price
  - `admin_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "order_type": "ride",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "client_id": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string"
}
```
- **Response (201 Created):**
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
  "price": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string",
  "created_at": "2025-08-11T08:48:03.183Z"
}
```

### 2.15 Get Order Price Breakdown

- **Endpoint:** `GET /admin/orders/{order_id}/price-breakdown`
- **Method:** `GET`
- **Path Parameters:**
  - `order_id` (string, required) — ID of the order
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "order_id": "string",
  "actual_price": 120.0,
  "distance_km": 10.5,
  "rate_per_km": 10.0,
  "minimum_fare": 50.0,
  "calculated_price": 105.0,
  "should_be_price": 105.0,
  "minimum_fare_applied": false,
  "is_custom_price": true,
  "difference": 15.0,
  "order_status": "completed",
  "created_at": "2025-08-11T08:45:49.071Z"
}
```

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
### 2.20 Create In-House Order

- **Endpoint:** `POST /admin/orders/in-house`
- **Method:** `POST`
- **Query Parameters:**
  - `admin_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "order_type": "ride",
  "pickup_address": "string",
  "pickup_latitude": "string",
  "pickup_longitude": "string",
  "dropoff_address": "string",
  "dropoff_latitude": "string",
  "dropoff_longitude": "string",
  "distance_km": "string",
  "total_paid": "decimal",
  "payment_status": "string",
  "special_instructions": "string"
}
```
- **Response (201 Created):**
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
  "price": "string",
  "distance_km": "string",
  "special_instructions": "string",
  "patient_details": "string",
  "medical_items": "string",
  "created_at": "2025-08-11T08:48:03.183Z"
}
```
```
---

## 3. Data Types and Enums

### Order Types
- `"ride"` — Standard ride service
- `"medical"` — Medical transport service
- `"delivery"` — Package delivery service

### Order Status
- `"pending"` — Order created, awaiting driver assignment
- `"accepted"` — Driver assigned and accepted
- `"in_progress"` — Order in progress
- `"completed"` — Order completed successfully
- `"cancelled"` — Order cancelled

### User Roles
- `"client"` — Regular customer
- `"driver"` — Service driver
- `"admin"` — Administrator

---

## 4. Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid input data or missing required fields"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Invalid or missing admin_key"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## 5. Usage Examples

### Get All Clients
```bash
curl -X GET "/admin/clients?admin_key=admin_secret_key_123"
```

### Create Order
```bash
curl -X POST "/admin/orders?admin_key=admin_secret_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "ride",
    "pickup_address": "123 Main St",
    "pickup_latitude": "-25.7479",
    "pickup_longitude": "28.2293",
    "dropoff_address": "456 Oak Ave",
    "dropoff_latitude": "-25.7580",
    "dropoff_longitude": "28.2400",
    "client_id": "client_123",
    "distance_km": "5.2",
    "special_instructions": "Please wait at the gate"
  }'
```

### Delete Order
```bash
curl -X DELETE "/admin/orders/order_123?admin_key=admin_secret_key_123"
```

### Calculate Price Preview
```bash
curl -X POST "/admin/pricing/calculate?distance_km=10.5&admin_key=Maurice@12!"
```

### Override Order Price
```bash
curl -X PATCH "/admin/orders/order_123/price?new_price=150.0&reason=Special%20discount&admin_key=Maurice@12!"
```

### Update Order Status
```bash
curl -X PATCH "/admin/orders/order_123/status?new_status=completed&admin_key=Maurice@12!"
```

### Search Orders
```bash
### Create In-House Order
```bash
curl -X POST "/admin/orders/in-house?admin_key=Maurice@12!" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "parcel_delivery",
    "pickup_address": "Warehouse A",
    "pickup_latitude": "-26.2041",
    "pickup_longitude": "28.0473",
    "dropoff_address": "Customer B",
    "dropoff_latitude": "-26.1952",
    "dropoff_longitude": "28.0341",
    "distance_km": "12.5",
    "total_paid": 125.00,
    "payment_status": "completed"
  }'
```
curl -X GET "/admin/orders/search?client_email=client@example.com&status=completed&admin_key=Maurice@12!"
```

### Get Admin Stats
```bash
curl -X GET "/admin/stats/summary?days=30&admin_key=Maurice@12!"
```

### Toggle Driver Availability
```bash
curl -X POST "/admin/drivers/driver_123/toggle-availability?admin_key=Maurice@12!"
```

### Apply Pricing Preset
```bash
curl -X POST "/admin/pricing/preset/rush_hour?admin_key=Maurice@12!"
```

### Get Pricing Presets
```bash
curl -X GET "/admin/pricing/presets?admin_key=Maurice@12!"
```

### Create Order with Custom Price
```bash
curl -X POST "/admin/orders/create-with-custom-price?custom_price=200.0&admin_key=Maurice@12!" \
  -H "Content-Type: application/json" \
  -d '{
    "order_type": "ride",
    "pickup_address": "123 Main St",
    "pickup_latitude": "-25.7479",
    "pickup_longitude": "28.2293",
    "dropoff_address": "456 Oak Ave",
    "dropoff_latitude": "-25.7580",
    "dropoff_longitude": "28.2400",
    "client_id": "client_123",
    "distance_km": "5.2",
    "special_instructions": "Please wait at the gate"
  }'
```

### Get Order Price Breakdown
```bash
curl -X GET "/admin/orders/order_123/price-breakdown?admin_key=Maurice@12!"
```

---

## 6. Notes

- All endpoints require HTTPS in production
- Timestamps are in ISO 8601 format (UTC)
- Latitude and longitude are stored as strings for precision
- The admin key should be kept secure and rotated regularly
- Rate limiting may apply to prevent abuse
- All numeric values (price, distance) are stored as strings to maintain precision
- The admin key has been updated to `Maurice@12!` for all new endpoints
