# Client and Driver Payment API Guide

This guide documents the API endpoints related to payment management for both clients and drivers.

---

## 1. Authentication

**Requirement:**
- `client_key` (string, required) — Secret key for client access
- `driver_key` (string, required) — Secret key for driver access
- All client requests must include `?client_key=your_client_secret`
- All driver requests must include `?driver_key=your_driver_secret`
- Base URL prefix: `/api`

---

## 2. API Endpoints

### 2.1 Get Client Payment History

- **Endpoint:** `GET /client/payments/history`
- **Method:** `GET`
- **Query Parameters:**
  - `client_key` (string, required) — Authentication key
  - `client_id` (string, required) — ID of the client
  - `limit` (integer, optional) — Number of results to return (default: 20, max: 100)
- **Response (200 OK):**
```json
[
  {
    "payment_id": "string",
    "order_id": "string",
    "amount": "decimal",
    "currency": "string",
    "status": "completed",
    "payment_method": "card",
    "transaction_date": "2025-08-13T10:00:00Z"
  }
]
```

### 2.2 Initiate Payment

- **Endpoint:** `POST /client/payments/initiate`
- **Method:** `POST`
- **Query Parameters:**
  - `client_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "client_id": "string",
  "order_id": "string",
  "amount": "decimal",
  "currency": "string",
  "payment_method": "card",
  "card_details": {
    "card_number": "string",
    "expiry_date": "string",
    "cvv": "string"
  }
}
```
- **Response (201 Created):**
```json
{
  "payment_id": "string",
  "order_id": "string",
  "amount": "decimal",
  "currency": "string",
  "status": "pending",
  "transaction_date": "2025-08-13T10:05:00Z",
  "message": "Payment initiated successfully"
}
```

### 2.3 Get Payment Status

- **Endpoint:** `GET /client/payments/{payment_id}/status`
- **Method:** `GET`
- **Path Parameters:**
  - `payment_id` (string, required) — ID of the payment
- **Query Parameters:**
  - `client_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "payment_id": "string",
  "order_id": "string",
  "status": "completed",
  "amount": "decimal",
  "currency": "string",
  "transaction_date": "2025-08-13T10:05:00Z"
}
```

### 2.4 Cancel Payment

- **Endpoint:** `POST /client/payments/{payment_id}/cancel`
- **Method:** `POST`
- **Path Parameters:**
  - `payment_id` (string, required) — ID of the payment to cancel
- **Query Parameters:**
  - `client_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "payment_id": "string",
  "status": "cancelled",
  "message": "Payment cancelled successfully"
}
```

### 2.5 Get Driver Earnings

- **Endpoint:** `GET /driver/earnings/history`
- **Method:** `GET`
- **Query Parameters:**
  - `driver_key` (string, required) — Authentication key
  - `driver_id` (string, required) — ID of the driver
  - `start_date` (string, optional) — Start date for earnings period (YYYY-MM-DD)
  - `end_date` (string, optional) — End date for earnings period (YYYY-MM-DD)
- **Response (200 OK):**
```json
{
  "driver_id": "string",
  "total_earnings": "decimal",
  "period_start": "2025-08-01",
  "period_end": "2025-08-13",
  "trips_completed": 25,
  "earnings_breakdown": [
    {
      "order_id": "string",
      "amount": "decimal",
      "date": "2025-08-10"
    }
  ]
}
```

### 2.6 Request Payout

- **Endpoint:** `POST /driver/payouts/request`
- **Method:** `POST`
- **Query Parameters:**
  - `driver_key` (string, required) — Authentication key
- **Request Body:**
```json
{
  "driver_id": "string",
  "amount": "decimal",
  "currency": "string",
  "payout_method": "bank_transfer",
  "bank_details": {
    "account_number": "string",
    "bank_name": "string",
    "swift_code": "string"
  }
}
```
- **Response (201 Created):**
```json
{
  "payout_id": "string",
  "driver_id": "string",
  "amount": "decimal",
  "currency": "string",
  "status": "pending",
  "request_date": "2025-08-13T10:15:00Z",
  "message": "Payout request submitted successfully"
}
```

### 2.7 Get Payout Status

- **Endpoint:** `GET /driver/payouts/{payout_id}/status`
- **Method:** `GET`
- **Path Parameters:**
  - `payout_id` (string, required) — ID of the payout
- **Query Parameters:**
  - `driver_key` (string, required) — Authentication key
- **Response (200 OK):**
```json
{
  "payout_id": "string",
  "driver_id": "string",
  "amount": "decimal",
  "currency": "string",
  "status": "completed",
  "request_date": "2025-08-13T10:15:00Z",
  "completion_date": "2025-08-14T10:00:00Z"
}
```

---

## 3. Data Types and Enums

### Payment Status
- `"pending"` — Payment initiated, awaiting confirmation
- `"completed"` — Payment successfully processed
- `"failed"` — Payment failed
- `"refunded"` — Payment refunded
- `"cancelled"` — Payment cancelled

### Payment Methods
- `"card"` — Credit/Debit Card
- `"paypal"` — PayPal
- `"bank_transfer"` — Bank Transfer
- `"mobile_money"` — Mobile Money

### Payout Status
- `"pending"` — Payout requested, awaiting processing
- `"processing"` — Payout being processed
- `"completed"` — Payout successfully transferred
- `"failed"` — Payout failed

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
  "message": "Invalid or missing authentication key"
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

### Get Client Payment History
```bash
curl -X GET "/client/payments/history?client_id=client_123&client_key=your_client_secret"
```

### Initiate Payment
```bash
curl -X POST "/client/payments/initiate?client_key=your_client_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "client_123",
    "order_id": "order_abc",
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "card",
    "card_details": {
      "card_number": "4111xxxxxxxx1111",
      "expiry_date": "12/25",
      "cvv": "123"
    }
  }'
```

### Get Payment Status
```bash
curl -X GET "/client/payments/payment_xyz/status?client_key=your_client_secret"
```

### Cancel Payment
```bash
curl -X POST "/client/payments/payment_xyz/cancel?client_key=your_client_secret"
```

### Get Driver Earnings
```bash
curl -X GET "/driver/earnings/history?driver_id=driver_456&driver_key=your_driver_secret&start_date=2025-08-01"
```

### Request Payout
```bash
curl -X POST "/driver/payouts/request?driver_key=your_driver_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "driver_456",
    "amount": 250.00,
    "currency": "USD",
    "payout_method": "bank_transfer",
    "bank_details": {
      "account_number": "1234567890",
      "bank_name": "Example Bank",
      "swift_code": "EXAMPLSWIFT"
    }
  }'
```

### Get Payout Status
```bash
curl -X GET "/driver/payouts/payout_uvw/status?driver_key=your_driver_secret"
```

---

## 6. Notes

- All endpoints require HTTPS in production.
- Timestamps are in ISO 8601 format (UTC).
- All numeric values (amount, earnings) are stored as strings to maintain precision.
- Authentication keys should be kept secure and rotated regularly.
- Rate limiting may apply to prevent abuse.
