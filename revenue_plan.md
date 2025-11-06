**Project: Revenue Tracking System Implementation Plan**

**Goal:** Implement a comprehensive system for tracking client payments, payment history, revenue, and calculating profits after driver payments. This plan outlines the necessary architectural changes, database migrations, API route implementations, and system logic required to successfully deploy the new revenue tracking functionality.

**Architecture Mode: Planning and Documentation**

**Deliverable:** `revenue_plan.md` (Full Comprehensive Plan)

---

### 1. Overview and Objectives

The current system lacks robust tracking for client payments, driver payment history, and accurate revenue/profit calculation. This project aims to rectify this by introducing dedicated database models, API endpoints, and business logic to ensure accurate, auditable financial tracking.

**Key Objectives:**

*   Successfully track all client payments (invoices, amounts, dates, status).
*   Successfully track all driver payments (requests, approvals, disbursements).
*   Calculate gross revenue.
*   Calculate net profit (Gross Revenue - Driver Payments - Operational Costs [if applicable, specify scope]).
*   Maintain a complete, searchable payment history for both clients and drivers.

### 2. Database Schema Enhancements (Alembic Migrations)

We require new tables and modifications to existing tables.

**A. New Table: `payments`**

| Field Name | Data Type | Description | Relationships |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer (PK) | Unique Payment ID | |
| `client_id` | UUID/Integer (FK) | Client making the payment | `clients.id` |
| `request_id` | UUID/Integer (FK) | Associated service request/trip | `requests.id` |
| `amount` | Numeric(10, 2) | Total amount paid by the client | |
| `payment_date` | DateTime | Date and time payment was received | |
| `payment_method` | String | e.g., 'Credit Card', 'Cash', 'Transfer' | |
| `status` | Enum/String | 'Pending', 'Completed', 'Failed', 'Refunded' | |
| `transaction_id` | String | External payment gateway transaction ID | |
| `created_at` | DateTime | Record creation timestamp | |
| `updated_at` | DateTime | Last update timestamp | |

**B. New Table: `driver_payouts`**

This table tracks payments made *to* drivers (the system's expense).

| Field Name | Data Type | Description | Relationships |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer (PK) | Unique Payout ID | |
| `driver_id` | UUID/Integer (FK) | Driver receiving the payout | `drivers.id` |
| `request_id` | UUID/Integer (FK) | Associated service request/trip | `requests.id` |
| `payout_amount` | Numeric(10, 2) | Amount paid to the driver | |
| `payout_date` | DateTime | Date and time payout was disbursed | |
| `payout_status` | Enum/String | 'Requested', 'Approved', 'Disbursed', 'Failed' | |
| `payment_request_ref` | String | Internal reference for the driver's request | |
| `disbursement_method` | String | e.g., 'Bank Transfer', 'Wallet' | |
| `created_at` | DateTime | Record creation timestamp | |
| `updated_at` | DateTime | Last update timestamp | |

**C. Alembic Migration Strategy**

1.  Generate migration script (`alembic revision --autogenerate -m "Add payments and driver_payouts tables"`).
2.  Review and refine the generated script to ensure proper indexing (e.g., on `client_id`, `driver_id`, `payment_date`).
3.  Apply migration to development/staging environments.

### 3. API Route Implementation (Missing Routes)

We need dedicated endpoints for recording payments, managing driver payout requests, and retrieving financial reports.

**A. Client Payment Routes (`/api/v1/payments`)**

| Method | Route | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/payments` | Record a new client payment (triggered post-transaction). | Internal/System |
| `GET` | `/payments/{id}` | Retrieve details of a specific payment. | Admin/Client (Self) |
| `GET` | `/payments/client/{client_id}` | Retrieve all payment history for a client. | Admin/Client (Self) |

**B. Driver Payout Routes (`/api/v1/payouts`)**

| Method | Route | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/payouts/request` | Driver submits a payment request for accumulated earnings. | Driver |
| `GET` | `/payouts/driver/{driver_id}` | Retrieve payout history for a specific driver. | Admin/Driver (Self) |
| `PUT` | `/payouts/{id}/status` | Update the status of a payout request (Approval/Disbursement). | Admin/Finance |

**C. Revenue Reporting Routes (`/api/v1/reports`)**

| Method | Route | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/reports/revenue` | Calculate and return gross revenue for a specified period (date range required). | Admin/Finance |
| `GET` | `/reports/profits` | Calculate and return net profit (Revenue - Payouts) for a specified period. | Admin/Finance |
| `GET` | `/reports/history` | Detailed ledger view of all payments and payouts within a period. | Admin/Finance |

### 4. Business Logic and Service Layer Implementation

The core logic must handle the relationship between client payments and driver earnings.

**A. Payment Processing Logic**

*   **Validation:** Ensure payment amounts match the associated service request/invoice.
*   **Idempotency:** Implement checks to prevent duplicate payment records using `transaction_id`.
*   **Status Update:** Upon successful payment recording, update the status of the associated `request` (e.g., from 'Pending Payment' to 'Completed').

**B. Driver Payout Logic**

*   **Earning Calculation:** A service layer function must calculate the total eligible earnings for a driver based on completed, paid requests since their last payout.
*   **Request Handling:** When a driver requests a payout, the system locks the associated earnings and creates a `driver_payouts` record with status 'Requested'.
*   **Disbursement:** Upon admin approval, the system updates the status to 'Disbursed' and records the `payout_date`.

**C. Revenue and Profit Calculation Logic**

*   **Gross Revenue:** Sum of `amount` from the `payments` table where `status` is 'Completed' within the specified date range.
*   **Total Payouts (Cost):** Sum of `payout_amount` from the `driver_payouts` table where `payout_status` is 'Disbursed' within the specified date range.
*   **Net Profit:** Gross Revenue - Total Payouts.

### 5. Integration Points

*   **Payment Gateway Integration:** Ensure the successful payment webhook/callback triggers the `POST /payments` route to record the transaction immediately.
*   **Driver App/Portal:** Update the driver interface to allow submission of payout requests and viewing of payout history.
*   **Admin Dashboard:** Develop new views for:
    *   Viewing the payment ledger.
    *   Reviewing and approving driver payout requests.
    *   Displaying the Revenue/Profit reports.

### 6. Testing and Validation

*   **Unit Tests:** Cover all new service layer functions (e.g., profit calculation, earning aggregation).
*   **Integration Tests:** Verify that API routes correctly interact with the database and that status updates propagate correctly (e.g., successful payment updates request status).
*   **Financial Reconciliation Tests:** Run reports against known test data to ensure calculated revenue and profit figures are mathematically accurate.

### 7. Deployment Strategy

1.  Deploy the Alembic migration to staging.
2.  Deploy the new API routes and service logic to staging.
3.  Thorough UAT (User Acceptance Testing) by the finance and operations teams.
4.  Scheduled production deployment, ensuring database migration is executed first.