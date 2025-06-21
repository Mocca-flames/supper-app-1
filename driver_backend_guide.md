# Driver Backend API Guide

This guide provides detailed information for drivers interacting with the backend API. It covers authentication, available endpoints, request formats, and expected responses.

## Table of Contents
1.  [Authentication](#authentication)
    *   [Firebase Google Sign-In](#firebase-google-sign-in)
    *   [API Token](#api-token)
2.  [Driver Endpoints](#driver-endpoints)
    *   [Get Available Orders](#get-available-orders)
    *   [Accept an Order](#accept-an-order)
    *   [Get My Orders](#get-my-orders)
    *   [Update Order Status](#update-order-status)
    *   [Update Driver Location](#update-driver-location)
3.  [Common Schemas](#common-schemas)
    *   [OrderResponse](#orderresponse)
    *   [OrderStatus Enum](#orderstatus-enum)
    *   [OrderType Enum](#ordertype-enum)

## 1. Authentication

### Firebase Google Sign-In
Driver authentication is handled via Firebase Google Sign-In.
1.  The driver signs in using their Google account through the client application.
2.  Upon successful authentication with Firebase, Firebase provides a unique User ID (`uid`).
3.  This `uid` is used as the `driver_id` in our backend system.
4.  When the user (driver) is registered in our system, their `user_role` is set to `driver`.

### API Token
All requests to the driver-specific endpoints must be authenticated.
After successful Firebase Google Sign-In, the client application will receive a Firebase ID Token. This token must be sent in the `Authorization` header with the `Bearer` scheme for every API request to protected driver endpoints.

**Example Header:**
```
Authorization: Bearer <YOUR_FIREBASE_ID_TOKEN>
```

The backend uses middleware (`get_current_driver`) to verify this token and identify the authenticated driver.

## 2. Driver Endpoints

All driver endpoints are prefixed with `/driver`.

---

### Get Available Orders
Retrieves a list of all orders currently in 'pending' status, available for drivers to accept.

*   **Method:** `GET`
*   **Path:** `/driver/available-orders`
*   **Authentication:** Required (Driver role)
*   **Request Body:** None
*   **Successful Response (200 OK):**
    *   **Type:** `List[OrderResponse]`
    *   **Description:** A list of order objects. See [OrderResponse](#orderresponse) for details.
    *   **Example:**
        ```json
        [
          {
            "id": "order_uuid_1",
            "client_id": "client_uuid_1",
            "driver_id": null,
            "order_type": "food_delivery",
            "status": "pending",
            "pickup_address": "123 Restaurant St, Food City",
            "pickup_latitude": "34.0522",
            "pickup_longitude": "-118.2437",
            "dropoff_address": "456 Customer Ave, Food City",
            "dropoff_latitude": "34.0522",
            "dropoff_longitude": "-118.2437",
            "price": null,
            "distance_km": null,
            "special_instructions": "Extra ketchup please",
            "created_at": "2025-06-11T10:00:00Z"
          }
        ]
        ```

---

### Accept an Order
Allows a driver to accept a pending order.

*   **Method:** `POST`
*   **Path:** `/driver/accept-order/{order_id}`
    *   `{order_id}`: The unique identifier of the order to accept.
*   **Authentication:** Required (Driver role)
*   **Request Body:**
    *   **Type:** `application/json`
    *   **Schema:** `OrderAccept`
        ```json
        {
          "driver_id": "string", // Must match the authenticated driver's ID
          "estimated_price": "decimal" // e.g., 15.75
        }
        ```
    *   **Fields:**
        *   `driver_id` (string, required): The ID of the driver accepting the order. This *must* match the `driver_id` of the authenticated driver making the request.
        *   `estimated_price` (decimal, required): The driver's estimated price for completing the order.
*   **Successful Response (200 OK):**
    *   **Type:** `OrderResponse`
    *   **Description:** The updated order object, now with `driver_id` populated and status potentially changed to `accepted`. See [OrderResponse](#orderresponse).
    *   **Example:**
        ```json
        {
          "id": "order_uuid_1",
          "client_id": "client_uuid_1",
          "driver_id": "driver_uuid_xyz", // Authenticated driver's ID
          "order_type": "food_delivery",
          "status": "accepted",
          "pickup_address": "123 Restaurant St, Food City",
          // ... other fields ...
          "price": 15.75, // Updated with estimated_price
          "created_at": "2025-06-11T10:00:00Z"
        }
        ```
*   **Error Responses:**
    *   `403 Forbidden`: If `accept_data.driver_id` does not match `current_driver.driver_id`.
    *   `404 Not Found`: If the `order_id` does not exist or the order is not in a state to be accepted.

---

### Get My Orders
Retrieves a list of all orders assigned to the currently authenticated driver.

*   **Method:** `GET`
*   **Path:** `/driver/my-orders`
*   **Authentication:** Required (Driver role)
*   **Request Body:** None
*   **Successful Response (200 OK):**
    *   **Type:** `List[OrderResponse]`
    *   **Description:** A list of order objects assigned to the driver. See [OrderResponse](#orderresponse).

---

### Update Order Status
Allows a driver to update the status of an order they are assigned to.

*   **Method:** `PUT`
*   **Path:** `/driver/orders/{order_id}/status`
    *   `{order_id}`: The unique identifier of the order to update.
*   **Authentication:** Required (Driver role)
*   **Request Body:**
    *   **Type:** `application/json`
    *   **Schema:** `OrderStatusUpdate`
        ```json
        {
          "status": "string" // Must be one of the OrderStatus enum values
        }
        ```
    *   **Fields:**
        *   `status` (string, required): The new status for the order. Must be a valid value from the [OrderStatus Enum](#orderstatus-enum) (e.g., "picked_up", "in_transit", "delivered").
*   **Successful Response (200 OK):**
    *   **Type:** `OrderResponse`
    *   **Description:** The updated order object with the new status. See [OrderResponse](#orderresponse).
*   **Error Responses:**
    *   `403 Forbidden`: If the authenticated driver is not assigned to this order.
    *   `404 Not Found`: If the `order_id` does not exist.
    *   `422 Unprocessable Entity`: If the provided status is invalid.

---

### Update Driver Location
Allows a driver to update their current geographical location. This is typically sent periodically.

*   **Method:** `POST`
*   **Path:** `/driver/location`
*   **Authentication:** Required (Driver role)
*   **Request Body:**
    *   **Type:** `application/json`
    *   **Schema:** `DriverLocationUpdate`
        ```json
        {
          "latitude": "float",
          "longitude": "float"
        }
        ```
    *   **Fields:**
        *   `latitude` (float, required): The driver's current latitude.
        *   `longitude` (float, required): The driver's current longitude.
*   **Successful Response (200 OK):**
    ```json
    {
      "message": "Location updated successfully"
    }
    ```

## 3. Common Schemas

### OrderResponse
This schema is used for representing order details in API responses.

```json
{
  "id": "string",                 // Unique order ID
  "client_id": "string",          // ID of the client who placed the order
  "driver_id": "string | null",   // ID of the driver assigned, or null
  "order_type": "string",         // Type of order (see OrderType Enum)
  "status": "string",             // Current status of the order (see OrderStatus Enum)
  "pickup_address": "string",
  "pickup_latitude": "string | null",
  "pickup_longitude": "string | null",
  "dropoff_address": "string",
  "dropoff_latitude": "string | null",
  "dropoff_longitude": "string | null",
  "price": "decimal | null",      // Final or estimated price
  "distance_km": "decimal | null",// Estimated or actual distance
  "special_instructions": "string | null",
  "created_at": "datetime"        // ISO 8601 format (e.g., "2025-06-11T12:34:56.789Z")
}
```

### OrderStatus Enum
Possible values for the `status` field in an order.

*   `pending`: Order created, awaiting driver acceptance.
*   `accepted`: Driver has accepted the order.
*   `picked_up`: Driver has picked up the items/passenger.
*   `in_transit`: Driver is on the way to the drop-off location.
*   `delivered`: Items/passenger successfully delivered.
*   `completed`: Order fully processed and finalized (e.g., after payment confirmation).
*   `cancelled`: Order has been cancelled.

### OrderType Enum
Possible values for the `order_type` field in an order.

*   `ride`: A ride-sharing service.
*   `food_delivery`: Delivery of food items.
*   `parcel_delivery`: Delivery of general parcels.
*   `medical_product`: Delivery of medical products.
*   `patient_transport`: Transportation for patients.
