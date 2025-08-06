Here is a plan for the frontend development to support the project's progression, focusing on both client and driver functionalities:

__I. Client-Side Features:__

1. __Order Creation Flow:__

   - __UI Components__: Develop UI elements for selecting pickup and dropoff locations (e.g., using a map component or address search).
   - __Distance Calculation__: Integrate a JavaScript function to calculate the distance using the Haversine formula based on coordinates.
   - __Price Display__: Show the calculated price to the user before they confirm the order.
   - __API Integration__: Implement the `POST /api/client/orders` request to send order details, including `distance_km`, and handle the response to display the order status.

2. __Order Tracking:__

   - __Order Details View__: Display the current order status and driver information.
   - __Map Integration__: Use a map component to visualize the driver's real-time location.
   - __API Polling/WebSockets__: Implement logic to fetch driver location periodically via `GET /api/orders/{order_id}/location` or utilize WebSockets for real-time updates.
   - __Status Display__: Show the current order status updates.

3. __Order History:__

   - Fetch and display a list of past orders for the client.

__II. Driver-Side Features:__

1. __Available Orders List:__

   - __UI Components__: Display a list of pending orders fetched from `GET /api/driver/available-orders`.
   - __Order Details__: Show pickup/dropoff locations and the calculated price for each order.
   - __Accept Order Action__: Implement a mechanism for drivers to accept an order by sending a `POST /api/driver/accept-order/{order_id}` request. The payload should include `driver_id` and `estimated_price`.

2. __Active Order Management:__

   - __Order Details View__: Display the details of the accepted order.
   - __Location Updates__: Implement functionality to capture the driver's current location and send it to `POST /driver/location`.
   - __Status Updates__: Provide UI elements for drivers to update the order status (e.g., `ACCEPTED` to `PICKED_UP`, `PICKED_UP` to `IN_TRANSIT`, `IN_TRANSIT` to `DELIVERED`) using `PUT /driver/orders/{order_id}/status`.

3. __Driver Profile & Availability:__

   - Implement UI for drivers to manage their profile information and availability status.

This plan outlines the necessary frontend development tasks to complement the backend features and advance the project.
