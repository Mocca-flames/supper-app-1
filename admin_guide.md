# Admin Panel API Guide

This guide provides instructions for interacting with the Admin API endpoints from a Vue.js frontend. It covers authentication, fetching clients, drivers, and orders, as well as creating orders.

## 1. Authentication

Admin-specific endpoints are protected and require an `admin_key` for access. This key must be sent as a query parameter with each request.

**Example `admin_key` (for development only, change in production!):** `admin_secret_key_123`

All requests to admin endpoints should include `?admin_key=YOUR_ADMIN_KEY` in the URL.

## 2. Vue.js Frontend Integration

We recommend using a library like `axios` for making HTTP requests from your Vue.js application.

### Installation
If you haven't already, install axios:
```bash
npm install axios
# or
yarn add axios
```

### Basic Axios Setup
You can create an axios instance for your API calls. Create a file, e.g., `src/api.js` or `src/services/api.js`:

```javascript
// src/services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Your backend API base URL
const ADMIN_KEY = 'admin_secret_key_123'; // Store this securely, e.g., in environment variables

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Function to make admin requests
const adminRequest = (method, url, data = null) => {
  const config = {
    method,
    url: `${url}?admin_key=${ADMIN_KEY}`, // Append admin_key as a query parameter
  };
  if (data) {
    config.data = data;
  }
  return apiClient(config);
};

export default adminRequest;
```

You can then import `adminRequest` in your Vue components.

## 3. Admin API Endpoints

The base URL for these endpoints is `/admin`.

### 3.1. Get All Clients

**(Proposed Endpoint)** This endpoint would retrieve a list of all clients in the system.

*   **Endpoint:** `GET /admin/clients`
*   **Method:** `GET`
*   **Query Parameters:**
    *   `admin_key` (string, required): Your secret admin key.
*   **Successful Response (200 OK):**
    ```json
    [
      {
        "client_id": "firebase_uid_client1",
        "user": {
            "id": "firebase_uid_client1",
            "email": "client1@example.com",
            "full_name": "Client One",
            "phone_number": "1234567890",
            "role": "client",
            "is_active": true,
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2023-01-01T10:00:00Z"
        },
        "home_address": "123 Client St, Clientville"
        // ... other client-specific fields
      },
      // ... more clients
    ]
    ```
*   **Vue.js Example (using the `adminRequest` function):**
    ```javascript
    // In your Vue component
    import adminRequest from '@/services/api'; // Adjust path as needed

    export default {
      data() {
        return {
          clients: [],
          loading: false,
          error: null,
        };
      },
      methods: {
        async fetchClients() {
          this.loading = true;
          this.error = null;
          try {
            const response = await adminRequest('get', '/admin/clients');
            this.clients = response.data;
          } catch (err) {
            this.error = 'Failed to fetch clients: ' + (err.response?.data?.detail || err.message);
            console.error(err);
          } finally {
            this.loading = false;
          }
        },
      },
      created() {
        this.fetchClients();
      },
    };
    ```

### 3.2. Get All Drivers

**(Proposed Endpoint)** This endpoint would retrieve a list of all drivers in the system.

*   **Endpoint:** `GET /admin/drivers`
*   **Method:** `GET`
*   **Query Parameters:**
    *   `admin_key` (string, required): Your secret admin key.
*   **Successful Response (200 OK):**
    ```json
    [
      {
        "driver_id": "firebase_uid_driver1",
        "user": {
            "id": "firebase_uid_driver1",
            "email": "driver1@example.com",
            "full_name": "Driver One",
            "phone_number": "0987654321",
            "role": "driver",
            "is_active": true,
            "created_at": "2023-01-02T11:00:00Z",
            "updated_at": "2023-01-02T11:00:00Z"
        },
        "license_no": "DL123XYZ",
        "vehicle_type": "Sedan"
        // ... other driver-specific fields
      },
      // ... more drivers
    ]
    ```
*   **Vue.js Example:**
    ```javascript
    // In your Vue component
    import adminRequest from '@/services/api';

    export default {
      data() {
        return {
          drivers: [],
          loading: false,
          error: null,
        };
      },
      methods: {
        async fetchDrivers() {
          this.loading = true;
          this.error = null;
          try {
            const response = await adminRequest('get', '/admin/drivers');
            this.drivers = response.data;
          } catch (err) {
            this.error = 'Failed to fetch drivers: ' + (err.response?.data?.detail || err.message);
            console.error(err);
          } finally {
            this.loading = false;
          }
        },
      },
      created() {
        this.fetchDrivers();
      },
    };
    ```

### 3.3. Get All Orders

**(Proposed Endpoint)** This endpoint would retrieve a list of all orders in the system.

*   **Endpoint:** `GET /admin/orders`
*   **Method:** `GET`
*   **Query Parameters:**
    *   `admin_key` (string, required): Your secret admin key.
*   **Successful Response (200 OK):**
    ```json
    [
      {
        "id": "order_uuid_1",
        "client_id": "firebase_uid_client1",
        "driver_id": "firebase_uid_driver1",
        "order_type": "delivery",
        "status": "COMPLETED",
        "pickup_address": "100 Pickup Rd",
        "dropoff_address": "200 Dropoff Ave",
        "price": "15.50",
        // ... other order fields from OrderResponse schema
        "created_at": "2023-01-03T12:00:00Z",
        "updated_at": "2023-01-03T12:30:00Z"
      },
      // ... more orders
    ]
    ```
*   **Vue.js Example:**
    ```javascript
    // In your Vue component
    import adminRequest from '@/services/api';

    export default {
      data() {
        return {
          orders: [],
          loading: false,
          error: null,
        };
      },
      methods: {
        async fetchOrders() {
          this.loading = true;
          this.error = null;
          try {
            const response = await adminRequest('get', '/admin/orders');
            this.orders = response.data;
          } catch (err) {
            this.error = 'Failed to fetch orders: ' + (err.response?.data?.detail || err.message);
            console.error(err);
          } finally {
            this.loading = false;
          }
        },
      },
      created() {
        this.fetchOrders();
      },
    };
    ```

### 3.4. Admin Create Order

This endpoint allows an admin to create an order on behalf of a client.

*   **Endpoint:** `POST /admin/orders`
*   **Method:** `POST`
*   **Query Parameters:**
    *   `admin_key` (string, required): Your secret admin key.
*   **Request Body (`AdminOrderCreate` schema):**
    ```json
    {
      "client_id": "firebase_uid_of_client", // ID of the client for whom the order is being created
      "order_type": "delivery", // or "ride" or other defined types
      "pickup_address": "123 Main St, Anytown",
      "pickup_latitude": 34.0522,
      "pickup_longitude": -118.2437,
      "dropoff_address": "456 Oak Ave, Otherville",
      "dropoff_latitude": 34.0530,
      "dropoff_longitude": -118.2445,
      "special_instructions": "Handle with care.",
      "patient_details": "Optional: Patient Name, Room 101", // If applicable
      "medical_items": "Optional: Prescription meds, medical equipment" // If applicable
    }
    ```
*   **Successful Response (200 OK):** An `OrderResponse` object for the created order.
    ```json
    {
      "id": "new_order_uuid",
      "client_id": "firebase_uid_of_client",
      "driver_id": null, // Initially null
      "order_type": "delivery",
      "status": "PENDING", // Initial status
      "pickup_address": "123 Main St, Anytown",
      // ... other fields from OrderResponse schema
      "created_at": "2023-01-04T14:00:00Z",
      "updated_at": "2023-01-04T14:00:00Z"
    }
    ```
*   **Vue.js Example:**
    ```javascript
    // In your Vue component
    import adminRequest from '@/services/api';

    export default {
      data() {
        return {
          newOrderData: {
            client_id: '',
            order_type: 'delivery',
            pickup_address: '',
            pickup_latitude: 0,
            pickup_longitude: 0,
            dropoff_address: '',
            dropoff_latitude: 0,
            dropoff_longitude: 0,
            special_instructions: '',
            patient_details: '',
            medical_items: ''
          },
          createdOrder: null,
          loading: false,
          error: null,
        };
      },
      methods: {
        async submitNewOrder() {
          this.loading = true;
          this.error = null;
          try {
            // Ensure latitude/longitude are numbers if your schema expects them
            const payload = {
              ...this.newOrderData,
              pickup_latitude: parseFloat(this.newOrderData.pickup_latitude) || 0,
              pickup_longitude: parseFloat(this.newOrderData.pickup_longitude) || 0,
              dropoff_latitude: parseFloat(this.newOrderData.dropoff_latitude) || 0,
              dropoff_longitude: parseFloat(this.newOrderData.dropoff_longitude) || 0,
            };
            const response = await adminRequest('post', '/admin/orders', payload);
            this.createdOrder = response.data;
            // Optionally, refresh the orders list or show a success message
          } catch (err) {
            this.error = 'Failed to create order: ' + (err.response?.data?.detail || err.message);
            console.error(err);
          } finally {
            this.loading = false;
          }
        },
      },
    };
    ```

## 4. Error Handling

API errors will typically return a JSON response with a `detail` field explaining the error.

*   **400 Bad Request:** Invalid input data.
*   **403 Forbidden:** Invalid or missing `admin_key`.
*   **404 Not Found:** Resource not found.
*   **500 Internal Server Error:** An unexpected error occurred on the server.

Your Vue.js code should handle these errors gracefully, for example, by displaying messages to the user. The examples above include basic error handling.

---

**Note:** The endpoints for `GET /admin/clients`, `GET /admin/drivers`, and `GET /admin/orders` are proposed functionalities for a complete admin panel. Their implementation would require adding corresponding routes in `app/api/admin_routes.py` and service methods in `app/services/user_service.py` and `app/services/order_service.py` to fetch all relevant records from the database, protected by the `verify_admin_key` dependency.
