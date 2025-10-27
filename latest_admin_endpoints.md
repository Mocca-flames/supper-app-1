## Admin Endpoints Documentation

This document provides comprehensive documentation for all admin endpoints in the Supper Delivery system, following the style and structure of the order payment flow documentation.

### Authentication

All admin endpoints require authentication using the `admin_key` header parameter:
```
admin_key: Maurice@12!
```

### 1. Order Management

#### 1.1. Create Regular Order for Client

*   **Endpoint:** `POST /admin/orders` ([`admin_create_order`](app/api/admin_routes.py:44))
*   **Description:** Admin creates an order for a specific client with standard pricing calculation.
*   **Request (Body):** [`AdminOrderCreate`](app/schemas/order_schemas.py:22)
    ```json
    {
        "order_type": "ride_hailing",
        "pickup_address": "123 Main St, City",
        "pickup_latitude": "34.0522",
        "pickup_longitude": "-118.2437",
        "dropoff_address": "456 Oak Ave, City",
        "dropoff_latitude": "34.0522",
        "dropoff_longitude": "-118.2437",
        "client_id": "client-uuid-123",
        "distance_km": "10.5",
        "special_instructions": "Handle with care"
    }
    ```
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)
    ```json
    {
        "id": "order-uuid-123",
        "client_id": "client-uuid-123",
        "driver_id": null,
        "order_type": "ride_hailing",
        "status": "pending",
        "pickup_address": "123 Main St, City",
        "pickup_latitude": "34.0522",
        "pickup_longitude": "-118.2437",
        "dropoff_address": "456 Oak Ave, City",
        "dropoff_latitude": "34.0522",
        "dropoff_longitude": "-118.2437",
        "price": 105.00,
        "distance_km": 10.5,
        "special_instructions": "Handle with care",
        "created_at": "2025-10-27T13:53:00.000Z",
        "payment_status": "pending",
        "total_paid": 0.00,
        "total_refunded": 0.00
    }
    ```

#### 1.2. Create In-House Order (No Client Required)

*   **Endpoint:** `POST /admin/orders/in-house` ([`admin_create_in_house_order`](app/api/admin_routes.py:59))
*   **Description:** Admin creates an order without requiring a specific client. Uses placeholder client ID and sets payment as completed.
*   **Request (Body):** [`InHouseOrderCreate`](app/schemas/order_schemas.py:25)
    ```json
    {
        "order_type": "parcel_delivery",
        "pickup_address": "Admin Warehouse",
        "pickup_latitude": "-26.2041",
        "pickup_longitude": "28.0473",
        "dropoff_address": "Customer Address",
        "dropoff_latitude": "-26.1952",
        "dropoff_longitude": "28.0341",
        "distance_km": "15.5",
        "total_paid": 150.00,
        "payment_status": "completed",
        "special_instructions": "Fragile items"
    }
    ```
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)
    ```json
    {
        "id": "order-uuid-456",
        "client_id": "IN_HOUSE_CLIENT_ID",
        "driver_id": null,
        "order_type": "parcel_delivery",
        "status": "pending",
        "pickup_address": "Admin Warehouse",
        "pickup_latitude": "-26.2041",
        "pickup_longitude": "28.0473",
        "dropoff_address": "Customer Address",
        "dropoff_latitude": "-26.1952",
        "dropoff_longitude": "28.0341",
        "price": 155.00,
        "distance_km": 15.5,
        "special_instructions": "Fragile items",
        "created_at": "2025-10-27T13:53:00.000Z",
        "payment_status": "completed",
        "total_paid": 150.00,
        "total_refunded": 0.00
    }
    ```

#### 1.3. Create Order with Custom Price

*   **Endpoint:** `POST /admin/orders/create-with-custom-price` ([`admin_create_order_custom_price`](app/api/admin_routes.py:307))
*   **Description:** Admin creates an order with optional custom pricing override.
*   **Request (Body):** [`AdminOrderCreate`](app/schemas/order_schemas.py:22)
*   **Request (Query):** `custom_price` (Optional[Decimal])
    ```json
    {
        "order_type": "ride_hailing",
        "pickup_address": "123 Main St, City",
        "pickup_latitude": "34.0522",
        "pickup_longitude": "-118.2437",
        "dropoff_address": "456 Oak Ave, City",
        "dropoff_latitude": "34.0522",
        "dropoff_longitude": "-118.2437",
        "client_id": "client-uuid-123",
        "distance_km": "10.5"
    }
    ```
    Query: `?custom_price=200.00`
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)

#### 1.4. Get All Orders

*   **Endpoint:** `GET /admin/orders` ([`get_all_orders`](app/api/admin_routes.py:74))
*   **Description:** Admin retrieves all orders in the system.
*   **Response (Body):** `List[OrderResponse]`
    ```json
    [
        {
            "id": "order-uuid-123",
            "client_id": "client-uuid-123",
            "driver_id": "driver-uuid-456",
            "order_type": "ride_hailing",
            "status": "completed",
            "pickup_address": "123 Main St, City",
            "pickup_latitude": "34.0522",
            "pickup_longitude": "-118.2437",
            "dropoff_address": "456 Oak Ave, City",
            "dropoff_latitude": "34.0522",
            "dropoff_longitude": "-118.2437",
            "price": 105.00,
            "distance_km": 10.5,
            "created_at": "2025-10-27T13:53:00.000Z",
            "payment_status": "completed",
            "total_paid": 105.00,
            "total_refunded": 0.00
        }
    ]
    ```

#### 1.5. Search Orders

*   **Endpoint:** `GET /admin/orders/search` ([`search_orders`](app/api/admin_routes.py:212))
*   **Description:** Search and filter orders with multiple criteria.
*   **Request (Query Parameters):**
    - `client_email` (Optional[str]): Search by client email
    - `status` (Optional[str]): Filter by order status
    - `min_price` (Optional[Decimal]): Minimum price filter
    - `max_price` (Optional[Decimal]): Maximum price filter
    - `limit` (int): Number of results to return (default: 50, max: 500)
*   **Response (Body):**
    ```json
    {
        "total_found": 25,
        "orders": [
            {
                "id": "order-uuid-123",
                "client_id": "client-uuid-123",
                "order_type": "ride_hailing",
                "status": "completed",
                "price": 105.00,
                "payment_status": "completed",
                "total_paid": 105.00,
                "created_at": "2025-10-27T13:53:00.000Z"
            }
        ]
    }
    ```

#### 1.6. Update Order Price

*   **Endpoint:** `PATCH /admin/orders/{order_id}/price` ([`admin_override_order_price`](app/api/admin_routes.py:164))
*   **Description:** Admin manually overrides the price of an existing order.
*   **Request (Path):** `order_id` (str)
*   **Request (Query):**
    - `new_price` (Decimal): New price for the order
    - `reason` (Optional[str]): Reason for price override
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)

#### 1.7. Update Order Status

*   **Endpoint:** `PATCH /admin/orders/{order_id}/status` ([`admin_update_order_status`](app/api/admin_routes.py:185))
*   **Description:** Admin manually updates the status of an existing order.
*   **Request (Path):** `order_id` (str)
*   **Request (Query):** `new_status` (str): New status value
*   **Response (Body):**
    ```json
    {
        "message": "Order order-uuid-123 status updated to completed"
    }
    ```

#### 1.8. Delete Order

*   **Endpoint:** `DELETE /admin/orders/{order_id}` ([`admin_delete_order`](app/api/admin_routes.py:102))
*   **Description:** Admin permanently deletes an order from the system.
*   **Request (Path):** `order_id` (str)
*   **Response (Body):** [`OrderResponse`](app/schemas/order_schemas.py:25)

#### 1.9. Get Order Price Breakdown

*   **Endpoint:** `GET /admin/orders/{order_id}/price-breakdown` ([`get_order_price_breakdown`](app/api/admin_routes.py:324))
*   **Description:** Get detailed price breakdown analysis for an order.
*   **Request (Path):** `order_id` (str)
*   **Response (Body):**
    ```json
    {
        "order_id": "order-uuid-123",
        "actual_price": 105.00,
        "distance_km": 10.5,
        "rate_per_km": 10.00,
        "minimum_fare": 50.00,
        "calculated_price": 105.00,
        "should_be_price": 105.00,
        "minimum_fare_applied": false,
        "is_custom_price": false,
        "difference": 0.00,
        "order_status": "completed",
        "created_at": "2025-10-27T13:53:00.000Z"
    }
    ```

### 2. User Management

#### 2.1. Get All Drivers

*   **Endpoint:** `GET /admin/drivers` ([`get_all_drivers`](app/api/admin_routes.py:21))
*   **Description:** Admin retrieves all driver profiles with their details.
*   **Response (Body):** `List[DriverResponse]`
    ```json
    [
        {
            "driver_id": "driver-uuid-123",
            "license_no": "DL123456",
            "vehicle_type": "sedan",
            "is_available": true,
            "email": "driver@example.com",
            "full_name": "John Driver"
        }
    ]
    ```

#### 2.2. Get All Clients

*   **Endpoint:** `GET /admin/clients` ([`get_all_clients`](app/api/admin_routes.py:83))
*   **Description:** Admin retrieves all client profiles with their details.
*   **Response (Body):** `List[UserResponse]`
    ```json
    [
        {
            "id": "client-uuid-123",
            "client_id": "client-uuid-123",
            "full_name": "Jane Client",
            "email": "client@example.com",
            "phone_number": "+1234567890",
            "created_at": "2025-10-27T13:53:00.000Z"
        }
    ]
    ```

#### 2.3. Toggle Driver Availability

*   **Endpoint:** `POST /admin/drivers/{driver_id}/toggle-availability` ([`toggle_driver_availability`](app/api/admin_routes.py:249))
*   **Description:** Admin toggles a driver's availability status.
*   **Request (Path):** `driver_id` (str)
*   **Response (Body):**
    ```json
    {
        "message": "Driver availability toggled",
        "driver_id": "driver-uuid-123",
        "is_available": false
    }
    ```

### 3. Pricing Management

#### 3.1. Calculate Price Preview

*   **Endpoint:** `POST /admin/pricing/calculate` ([`calculate_price_preview`](app/api/admin_routes.py:122))
*   **Description:** Calculate price preview with optional custom rates.
*   **Request (Query):**
    - `distance_km` (Decimal): Distance in kilometers
    - `rate_per_km` (Optional[Decimal]): Custom rate per km
    - `minimum_fare` (Optional[Decimal]): Custom minimum fare
*   **Response (Body):**
    ```json
    {
        "distance_km": 10.5,
        "rate_per_km": 10.00,
        "minimum_fare": 50.00,
        "calculated_price": 105.00,
        "final_price": 105.00,
        "minimum_fare_applied": false
    }
    ```

#### 3.2. Apply Pricing Preset

*   **Endpoint:** `POST /admin/pricing/preset/{preset}` ([`apply_pricing_preset`](app/api/admin_routes.py:274))
*   **Description:** Apply predefined pricing presets for strategic control.
*   **Request (Path):** `preset` (str): rush_hour, off_peak, weekend, standard
*   **Response (Body):**
    ```json
    {
        "preset_applied": "rush_hour",
        "rate_per_km": 15.00,
        "minimum_fare": 70.00,
        "message": "Applied rush_hour pricing preset"
    }
    ```

#### 3.3. Get Pricing Presets

*   **Endpoint:** `GET /admin/pricing/presets` ([`get_pricing_presets`](app/api/admin_routes.py:295))
*   **Description:** Get available pricing presets with their configurations.
*   **Response (Body):**
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

### 4. Analytics and Statistics

#### 4.1. Get Admin Statistics Summary

*   **Endpoint:** `GET /admin/stats/summary` ([`get_admin_stats_summary`](app/api/admin_routes.py:235))
*   **Description:** Get comprehensive admin statistics for a specified period.
*   **Request (Query):** `days` (int): Number of days to analyze (default: 30, max: 365)
*   **Response (Body):**
    ```json
    {
        "period_days": 30,
        "period_start": "2025-09-27T00:00:00",
        "period_end": "2025-10-27T00:00:00",
        "total_orders": 1250,
        "orders_by_status": {
            "pending": 45,
            "accepted": 23,
            "in_transit": 67,
            "completed": 1100,
            "cancelled": 15
        },
        "total_revenue": 125000.00,
        "average_price": 100.00,
        "active_drivers": 25,
        "top_clients": [
            {
                "client_id": "client-uuid-123",
                "orders": 45
            }
        ]
    }
    ```

### 5. Error Handling

All admin endpoints follow consistent error handling patterns:

- **400 Bad Request:** Invalid input data or validation errors
- **403 Forbidden:** Invalid or missing admin authentication
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Unexpected server errors

Error responses include descriptive messages:
```json
{
    "detail": "Order with ID order-uuid-123 not found"
}
```

### 6. Admin Workflow Examples

#### 6.1. Complete Order Management Flow

1. **Create In-House Order:**
   ```
   POST /admin/orders/in-house
   {
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
   }
   ```

2. **Monitor Order Status:**
   ```
   GET /admin/orders/search?status=pending
   ```

3. **Assign Driver (if needed):**
   ```
   PATCH /admin/orders/{order_id}/status?new_status=accepted
   ```

4. **Track Performance:**
   ```
   GET /admin/stats/summary?days=7
   ```

#### 6.2. Pricing Management Flow

1. **Check Current Pricing:**
   ```
   GET /admin/pricing/presets
   ```

2. **Apply Rush Hour Pricing:**
   ```
   POST /admin/pricing/preset/rush_hour
   ```

3. **Override Specific Order Price:**
   ```
   PATCH /admin/orders/{order_id}/price?new_price=150.00&reason=Customer negotiation
   ```

### 7. Security Considerations

- All endpoints require admin authentication via `admin_key` header
- Input validation is performed on all parameters
- Database operations include proper error handling and rollback mechanisms
- Sensitive operations are logged for audit purposes

### 8. Performance Notes

- Search endpoints support pagination with configurable limits
- Statistics endpoints can analyze up to 365 days of data
- Large result sets are efficiently handled with database-level filtering
- Redis caching is used for frequently accessed data