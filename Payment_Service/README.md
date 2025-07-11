# EVISA Payment Service

This microservice handles payment initiation, status tracking, and webhook event processing for the Fiji eVisa Portal. Designed for integration with Stripe and Fijian payment providers.

## Endpoints

- `POST /payments/initiate`: Initiate a payment (choose provider: stripe or fijian)
- `GET /payments/{payment_id}/status`: Check status of a payment
- `POST /payments/events/stripe`: Webhook for Stripe payment events
- `POST /payments/events/fijian`: Webhook for Fijian gateway payment events
- `GET /payments/wsdoc`: Docs/help for real-time status integration

## Running Locally

Create a Python virtualenv and install dependencies:

```
cd Payment_Service
pip install -r requirements.txt
uvicorn main:app --reload
```

## Sample Payment Flow

1. Frontend posts to `/payments/initiate` with applicant ID and amount.
2. Redirect user to the returned URL for payment (mocked in the demo).
3. Payment provider sends an event/webhook on completion to `/payments/events/{provider}`.
4. The service updates status. Client polls `/payments/{payment_id}/status` or subscribes to updates (future: via websocket).

## Note
This is a scaffold/demo version with in-memory store and mock logic for integration testing and further development.
