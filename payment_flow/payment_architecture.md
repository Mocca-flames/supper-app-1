# Payment System Architecture Diagram

```mermaid
erDiagram

    USER {
        string id
        string email
        string name
        --
        has_many orders
        has_many payments
    }

    DRIVER {
        string driver_id
        string user_id
        string vehicle_details
        --
        has_many orders
        has_many payments
    }

    ORDER {
        string id
        string client_id
        string driver_id
        enum order_type
        enum status
        decimal price
        decimal distance_km
        enum payment_status
        decimal total_paid
        decimal total_refunded
        --
        belongs_to user
        belongs_to driver
        has_many payments
        has_many refunds
    }

    PAYMENT {
        string id
        string order_id
        string user_id
        enum payment_type
        decimal amount
        string currency
        enum payment_method
        enum status
        string transaction_id
        text transaction_details
        datetime created_at
        datetime updated_at
        --
        belongs_to order
        belongs_to user
        has_many refunds
    }

    REFUND {
        string id
        string payment_id
        string order_id
        decimal amount
        text reason
        enum status
        datetime processed_at
        datetime created_at
        datetime updated_at
        --
        belongs_to payment
        belongs_to order
    }

    PAYMENT_METHOD {
        enum value
        string display_name
    }

    PAYMENT_STATUS {
        enum value
        string display_name
    }

    PAYMENT_TYPE {
        enum value
        string display_name
    }

    USER ||--o{ ORDER : "creates"
    DRIVER ||--o{ ORDER : "accepts"
    ORDER ||--o{ PAYMENT : "has"
    PAYMENT ||--o{ REFUND : "can have"
    ORDER ||--o{ REFUND : "can have"
    USER ||--o{ PAYMENT : "makes"
    DRIVER ||--o{ PAYMENT : "receives"
    PAYMENT }|--|| PAYMENT_METHOD : "uses"
    PAYMENT }|--|| PAYMENT_STATUS : "has"
    PAYMENT }|--|| PAYMENT_TYPE : "is"
```

## Architecture Overview

### Components

1. **Users**: Clients who create orders and make payments
2. **Drivers**: Drivers who accept orders and receive payments
3. **Orders**: Core business entities that track delivery requests
4. **Payments**: Financial transactions related to orders
5. **Refunds**: Payment reversals when needed
6. **Enums**: Standardized types for payment methods, statuses, and types

### Relationships

- Users create orders and make payments
- Drivers accept orders and receive payments
- Orders have multiple payments (client payments and driver payments)
- Payments can have refunds
- Orders can have direct refunds (for simplicity)
- Payments use standardized methods, statuses, and types

### Workflow

1. **Order Creation**: Client creates an order with PENDING payment status
2. **Payment Processing**: Client makes payment(s) against the order
3. **Payment Status Updates**: As payments are processed, order payment status updates
4. **Order Completion**: When full payment is received, order can be completed
5. **Refunds**: If needed, payments can be refunded (partial or full)
6. **Driver Payments**: Separate payments track driver payouts