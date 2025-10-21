## Order Flow and Payments: Client Endpoint Perspective

This document details the interaction between clients, the backend API, and payment gateways for order creation and payment verification. The focus is on providing a clear, flexible, and easy-to-implement flow from the client's perspective.

### 1. Order Creation

The client initiates an order, which involves estimating the cost and then creating the order.

#### 1.1. Estimate Order Cost

Before creating an order, a client can request an estimate. This allows the client application to display potential costs to the user before committing to an order.

*   **Endpoint:** `POST /client/orders/estimate` ([`estimate_order_cost`](app/api/client_routes.py:29))
*   **Description:** Calculates the estimated price and distance for a potential order based on pickup and dropoff locations and service type.
*   **Request (Body):** [`OrderEstimateRequest`](app/schemas/order_schemas.py:60)
    ```json
    {
        "service_type": "ride_hailing",
        "pickup_latitude": 34.0522,
        "pickup_longitude": -118.2437,
        "dropoff_latitude": 34.0522,
        "dropoff_longitude": -118.2437,
        "passenger_count": 1,
        "vehicle_type": "standard"
    }
    ```
*   **Response (Body):** [`CostEstimationResponse`](app/schemas/order_schemas.py:85)
    ```json
    {
        "estimate": {
            "base_fare": 20.00,
            "distance_fare": 15.50,
            "service_fee": 2.50,
            "total": 38.00,
            "estimated_duration_minutes": 30,
            "currency": "ZAR",
            "surge_multiplier": 1.0,
            "medical_surcharge": 0.0,
            "package_surcharge": 0.0,
            "delivery_fee": 0.0
        },
        "valid_until": "2025-10-19T08:00:00Z",
        "special_instructions": null
    }
    ```

#### 1.2. Create Order

Once the client is satisfied with the estimate, they proceed to create the actual order. This step registers the order in the system, setting its initial payment status to `PENDING`.

*   **Endpoint:** `POST /client/orders` ([`create_order`](app/api/client_routes.py:18))
*   **Description:** Creates a new order in the system. The order's initial `payment_status` is `PENDING`.
*   **Request (Body):** [`OrderCreate`](app/schemas/order_schemas.py:8)
    ```json
    {
        "order_type": "ride_hailing",
        "pickup_address": "123 Main St, City",
        "pickup_latitude": "34.0522",
        "pickup_longitude": "-118.2437",
        "dropoff_address": "456 Oak Ave, City",
        "dropoff_latitude": "34.0522",
        "dropoff_longitude": "-118.2437",
        "client_id": "some-client-uuid",
        "distance_km": "10.5",
        "special_instructions": "Be careful with fragile items."
    }
    ```
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)
    ```json
    {
        "id": "order-uuid-123",
        "client_id": "some-client-uuid",
        "driver_id": null,
        "order_type": "ride_hailing",
        "status": "pending",
        "pickup_address": "123 Main St, City",
        "pickup_latitude": "34.0522",
        "pickup_longitude": "-118.2437",
        "dropoff_address": "456 Oak Ave, City",
        "dropoff_longitude": "-118.2437",
        "price": 38.00,
        "distance_km": 10.5,
        "special_instructions": "Be careful with fragile items.",
        "created_at": "2025-10-19T07:30:00.000Z",
        "payment_status": "pending",
        "total_paid": 0.00,
        "total_refunded": 0.00
    }
    ```

### 2. Payment Initialization

After an order is created, the client needs to initiate a payment for it. This example focuses on Paystack, but the pattern is adaptable to other gateways. The client application will receive a redirect URL to complete the payment on the chosen gateway's platform.

#### 2.1. Initialize Paystack Payment

*   **Endpoint:** `POST /payment/paystack/initialize` ([`initialize_paystack_payment`](app/api/payment_routes.py:30))
*   **Description:** Initiates a payment transaction with Paystack. The backend creates a `Payment` record with `PENDING` status and returns an `authorization_url` for the client to redirect to and complete the payment.
*   **Request (Body):** [`PaymentCreate`](app/schemas/payment_schemas.py:7) (with `gateway` set to `PAYSTACK`)
    ```json
    {
        "order_id": "order-uuid-123",
        "user_id": "some-client-uuid",
        "payment_type": "client_payment",
        "amount": 38.00,
        "currency": "ZAR",
        "payment_method": "credit_card",
        "gateway": "paystack"
    }
    ```
*   **Response (Body):** (Custom response, containing a `PaymentResponse` and a `redirect_url`)
    ```json
    {
        "payment": {
            "id": "payment-uuid-456",
            "order_id": "order-uuid-123",
            "user_id": "some-client-uuid",
            "payment_type": "client_payment",
            "amount": 38.00,
            "currency": "ZAR",
            "payment_method": "credit_card",
            "gateway": "paystack",
            "status": "pending",
            "transaction_id": null,
            "created_at": "2025-10-19T07:35:00.000Z",
            "updated_at": "2025-10-19T07:35:00.000Z"
        },
        "authorization_url": "https://checkout.paystack.com/some-reference"
    }
    ```
    The client application should redirect the user to the `authorization_url` to complete the payment on the Paystack platform.

### 3. Payment Verification

After the client completes the payment on the gateway's side, the backend needs to verify the payment. This is primarily handled by webhooks for reliability, with a client-initiated verification as a fallback.

#### 3.1. Paystack Webhook (Server-to-Server - Primary Verification)

*   **Endpoint:** `POST /payment/paystack/webhook` ([`paystack_webhook`](app/api/payment_routes.py:434))
*   **Description:** This endpoint is called by Paystack's server to asynchronously notify the backend about the final status of a transaction (e.g., success, failure, reversal). This is the most reliable method for payment verification.
*   **Request (Body):** (Paystack's webhook payload, typically a JSON object containing `event` and `data` fields)
    ```json
    {
        "event": "charge.success",
        "data": {
            "id": 123456789,
            "domain": "test",
            "status": "success",
            "reference": "payment-uuid-456",
            "amount": 3800, // in kobo/cents
            "currency": "ZAR",
            "customer": {
                "id": 123,
                "email": "client@example.com"
            },
            // ... other Paystack specific details
        }
    }
    ```
*   **Response (Body):** (Typically an empty 200 OK response to acknowledge receipt of the webhook. This is crucial for Paystack to consider the webhook delivered.)
    ```json
    {}
    ```
    **Backend Logic:**
    1.  Receives the webhook from Paystack.
    2.  Verifies the webhook signature to ensure its authenticity.
    3.  Validates the payment amount does not exceed the remaining order balance.
    4.  Extracts the `reference` (which corresponds to our `payment.id`) and the transaction `status` from the payload.
    5.  Calls `PaymentService.update_payment_status` to update the `Payment` record in the database to `COMPLETED` (or `FAILED`/`REFUNDED` as appropriate).
    6.  Updates the associated `Order`'s `payment_status` to `COMPLETED` if the total paid amount for the order meets or exceeds the order's price.

#### 3.2. Paystack Callback / Manual Verification (Client-to-Server - Fallback)

*   **Endpoint:** `GET /payment/paystack/verify/{reference}` ([`verify_paystack_payment`](app/api/payment_routes.py:480))
*   **Description:** This endpoint can be used by the client application to manually verify a payment status. It's typically called after the user is redirected back from Paystack's payment page, serving as a fallback or an immediate confirmation mechanism.
*   **Request (Path Parameter):** `reference` (which is our `payment.id`)
*   **Response (Body):** [`PaymentResponse`](app/schemas/payment_schemas.py:18)
    ```json
    {
        "id": "payment-uuid-456",
        "order_id": "order-uuid-123",
        "user_id": "some-client-uuid",
        "payment_type": "client_payment",
        "amount": 38.00,
        "currency": "ZAR",
        "payment_method": "credit_card",
        "gateway": "paystack",
        "status": "completed", // Updated status
        "transaction_id": "paystack-txn-id-789",
        "created_at": "2025-10-19T07:35:00.000Z",
        "updated_at": "2025-10-19T07:40:00.000Z"
    }
    ```
    **Backend Logic:**
    1.  Receives the `reference` (payment ID) from the client.
    2.  Queries Paystack's API directly to get the official status of the transaction using the `reference`.
    3.  Updates the `Payment` record and the associated `Order`'s `payment_status` based on the response from Paystack.
    4.  Returns the updated `PaymentResponse` to the client.

### 4. How Order is Connected to Payments and Verification

The system maintains a clear connection between orders and payments through foreign keys and status fields, ensuring data consistency and accurate payment tracking.

*   **`Order` Model:** The [`Order`](app/models/order_models.py:26) model includes:
    *   `payment_status`: An `Enum` of [`PaymentStatus`](app/models/payment_models.py:13) (e.g., `PENDING`, `PARTIAL`, `COMPLETED`) that directly indicates the overall payment state of the order.
    *   `total_paid`: A `Numeric` field tracking the sum of all successfully completed payments for this order.
    *   `total_refunded`: A `Numeric` field tracking the sum of all processed refunds for this order.
    *   `payments`: A one-to-many relationship to the `Payment` model, allowing an order to have multiple associated payment transactions.
*   **`Payment` Model:** The [`Payment`](app/models/payment_models.py:30) model includes:
    *   `order_id`: A `ForeignKey` to `orders.id`, explicitly linking each payment record back to its parent order.
    *   `status`: An `Enum` of [`PaymentStatus`](app/models/payment_models.py:13) that indicates the individual payment transaction's lifecycle (e.g., `PENDING`, `COMPLETED`, `FAILED`, `REFUNDED`).
    *   `gateway`: An `Enum` of [`PaymentGateway`](app/models/payment_models.py:26) to specify which payment provider handled the transaction.
*   **Verification Logic in `PaymentService`:**
    *   The `PaymentService.update_payment_status` method is central to verification. When a payment gateway (via webhook or manual verification) confirms a transaction:
        1.  It updates the specific `Payment` record's `status` (e.g., to `COMPLETED`).
        2.  It then recalculates the `order.total_paid` by summing all `COMPLETED` client payments associated with that order.
        3.  Based on `order.total_paid` versus `order.price`, the `order.payment_status` is updated accordingly (`COMPLETED`, `PARTIAL`, or `PENDING`). This ensures the order's payment state accurately reflects all associated transactions.

### 5. High-Value Order Payment Flow (Mermaid Diagram)

```mermaid
sequenceDiagram
    actor Client
    participant Backend as API/Services
    participant PaymentGateway as Paystack/PayFast
    participant Database

    Client->>Backend: 1. Request Order Estimate (POST /client/orders/estimate)
    Backend->>Backend: Calculate Price (PricingService)
    Backend-->>Client: Order Estimate Response (CostEstimationResponse)

    Client->>Backend: 2. Create Order (POST /client/orders)
    Backend->>Database: Save Order (Status: PENDING, PaymentStatus: PENDING)
    Database-->>Backend: Order ID
    Backend-->>Client: Order Confirmation (OrderResponse)

    Client->>Backend: 3. Initialize Payment (POST /payment/paystack/initialize)
    Backend->>Database: Create Payment Record (Status: PENDING)
    Database-->>Backend: Payment ID
    Backend->>PaymentGateway: Request Payment Authorization URL
    PaymentGateway-->>Backend: Authorization URL
    Backend-->>Client: Payment Authorization URL

    Client->>PaymentGateway: 4. Redirect to Payment Gateway (Complete Payment)
    PaymentGateway->>PaymentGateway: Process Payment
    PaymentGateway->>Backend: 5. Webhook Notification (POST /payment/paystack/webhook)
    Backend->>Backend: Verify Webhook Signature
    Backend->>Database: Update Payment Status (COMPLETED)
    Backend->>Database: Recalculate Order.total_paid
    Backend->>Database: Update Order.payment_status (COMPLETED/PARTIAL)
    Database-->>Backend: Updated Order/Payment
    Backend-->>PaymentGateway: 200 OK

    Client->>Backend: 6. (Optional) Verify Payment Status (GET /payment/paystack/verify/{reference})
    Backend->>PaymentGateway: Query Transaction Status
    PaymentGateway-->>Backend: Transaction Status
    Backend->>Database: (If needed) Update Payment/Order Status
    Database-->>Backend: Updated Payment/Order
    Backend-->>Client: Payment Status (PaymentResponse)
