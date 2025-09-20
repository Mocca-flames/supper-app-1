# Client-Side Payment Gateway Integration Guide (PayFast.io)

This guide explains a secure PayFast integration where all credentials and signature generation happen on the backend. The client calls your FastAPI backend, which returns a signed form payload for submission to PayFast.

## Payment Process Overview

1. Client sends minimal payment data to backend.
2. Backend generates signed PayFast form data and returns payment_url and form_data.
3. Client submits form_data to PayFast.
4. PayFast processes payment and redirects to return_url or cancel_url.
5. Client extracts pf_payment_id from return_url and queries backend for status.
6. Backend queries PayFast and returns status to client.

## Prerequisites

- Backend POST /payments/create endpoint implemented.
- Backend GET /payments/query/{pf_payment_id} endpoint implemented.
- PayFast credentials configured server-side.
- Client can make authenticated HTTP requests.

## Client Steps

1. Prepare minimal payment payload (no credentials or signatures).

Example:

```javascript
const payload = {
  order_id: 'ORDER_UUID',
  amount: '100.00',
  payment_type: 'CLIENT_PAYMENT',
  payment_method: 'CARD',
  user_id: CURRENT_USER_ID // temporary, backend will derive this later
};
```

2. Initiate payment:

```javascript
async function initiatePayment(payload, token) {
  const response = await fetch('/payments/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  if (!response.ok || !result.payment_url || !result.form_data) {
    console.error('Payment initiation failed:', result.detail || result);
    return;
  }
  const form = document.createElement('form');
  form.action = result.payment_url;
  form.method = 'POST';
  Object.entries(result.form_data).forEach(([key, value]) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = key;
    input.value = value;
    form.appendChild(input);
  });
  document.body.appendChild(form);
  form.submit();
}
```

## Server Responsibilities

- Build PayFast form fields including credentials and URLs.
- Generate signature with sorted, URL-encoded key=value pairs and optional passphrase.
- Persist Payment record and return payment_url, form_data, and payment to client.

See [PaymentService.create_payment()](app/services/payment_service.py:24).

## Transaction Status Query

Client queries backend for payment status; backend calls PayFast.

```javascript
async function confirmPaymentStatus(pfPaymentId, token) {
  const res = await fetch(`/payments/query/${pfPaymentId}`, {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  return await res.json();
}
```

## Handling Return URLs

On success page:

```javascript
const urlParams = new URLSearchParams(window.location.search);
const pfPaymentId = urlParams.get('pf_payment_id');
if (pfPaymentId) {
  confirmPaymentStatus(pfPaymentId, token)
    .then(data => {
      if (data.status === 'success' && data.data && data.data.payment_status === 'COMPLETE') {
        onPaymentSuccess(data.data);
      } else if (data.data && data.data.payment_status) {
        onPaymentStatus(data.data.payment_status);
      } else {
        console.error('Unexpected payment status:', data);
        onPaymentError();
      }
    })
    .catch(() => onPaymentError());
}
```

On cancel page:

```javascript
onPaymentCancelled();
```

## Testing

- Use sandbox credentials.
- Test card and EFT flows.
- Simulate errors and verify messaging.
- Ensure no credentials leak client-side.

## Security

- Never expose credentials client-side.
- Use HTTPS everywhere.
- Validate orders and amounts server-side.
- Log payment events.
- Plan to derive user_id from auth context server-side.

## Backend API Notes

- POST /payments/create currently requires user_id; plan to derive from auth context.
- GET /payments/query/{pf_payment_id} is implemented for status confirmation.