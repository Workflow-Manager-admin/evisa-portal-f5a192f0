import os
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
import uuid
import logging

# Eventual DB and gateway integrations would go here.
# In this sample, payments are not persisted and actual gateway logic is mocked.

app = FastAPI(
    title="EVISA Payment Service",
    description="""
    The Payment Service handles payment processing for the Fiji eVisa portal, including payment initiation, status tracking, webhook event handling, and integration hooks for Stripe and Fijian payment gateways.
    """,
    version="1.0.0",
    openapi_tags=[
        {
            "name": "payments",
            "description": "Payment operations: creation, status, and webhook processing."
        },
        {
            "name": "integration",
            "description": "Hooks for payment gateway integrations (Stripe, Fijian providers)."
        }
    ]
)

# --- Models ---

class PaymentProvider(str, Enum):
    stripe = "stripe"
    fijian = "fijian"

class PaymentStatus(str, Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"

class PaymentInitRequest(BaseModel):
    applicant_id: str = Field(..., description="Unique identifier for the applicant.")
    amount: float = Field(..., description="The payment amount in FJD.")
    currency: str = Field("FJD", description="Currency code. Defaults to FJD.")
    provider: PaymentProvider = Field(..., description="The payment provider to use (stripe/fijian).")
    description: Optional[str] = Field(None, description="Optional description for the payment.")

class PaymentResponse(BaseModel):
    payment_id: str = Field(..., description="Unique payment identifier.")
    status: PaymentStatus = Field(..., description="Payment status.")
    redirect_url: Optional[str] = Field(None, description="Redirect URL to complete payment if applicable.")

class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    detail: Optional[str] = None

# --- In-memory store for illustrative purposes only ---
payment_store = {}

# PUBLIC_INTERFACE
@app.post("/payments/initiate", response_model=PaymentResponse, tags=["payments"], summary="Initiate a payment", description="Starts a new payment for a visa application. Returns a payment id and, if needed, a redirect URL to the payment gateway.")
async def initiate_payment(req: PaymentInitRequest, background_tasks: BackgroundTasks):
    """Starts a payment with the specified provider."""
    payment_id = str(uuid.uuid4())
    payment_store[payment_id] = {
        "status": PaymentStatus.pending,
        "provider": req.provider,
        "amount": req.amount,
        "applicant_id": req.applicant_id,
        "description": req.description,
        "currency": req.currency
    }

    if req.provider == PaymentProvider.stripe:
        # Simulate a Stripe redirect URL (normally generated on backend with Stripe API)
        redirect_url = f"https://payments.stripe.com/pay/{payment_id}"
        # In real-world, create a Stripe session and save intent details
    elif req.provider == PaymentProvider.fijian:
        # Simulate local provider (for demo, fake URL)
        redirect_url = f"https://fijian-gateway.com/initiate/{payment_id}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported payment provider.")

    logging.info(f"Payment initiated: {payment_id} for applicant {req.applicant_id}")
    # Simulate async status update (in production, rely on webhook/events)
    background_tasks.add_task(mock_process_payment, payment_id, req.provider)

    return PaymentResponse(
        payment_id=payment_id,
        status=PaymentStatus.pending,
        redirect_url=redirect_url
    )

# PUBLIC_INTERFACE
@app.get("/payments/{payment_id}/status", response_model=PaymentStatusResponse, tags=["payments"], summary="Get payment status", description="Returns the current status of a payment by payment_id.")
async def get_payment_status(payment_id: str):
    """Fetches the current payment status."""
    if payment_id not in payment_store:
        raise HTTPException(status_code=404, detail="Payment not found.")
    entry = payment_store[payment_id]
    return PaymentStatusResponse(
        payment_id=payment_id,
        status=entry["status"],
        detail=None
    )

# PUBLIC_INTERFACE
@app.post("/payments/events/stripe", tags=["integration"], summary="Stripe webhook endpoint", description="Webhook endpoint to receive events from Stripe and update payment status accordingly.")
async def stripe_webhook(request: Request):
    """Stripe event handler: receives Stripe webhook events and updates payment status accordingly"""
    payload = await request.json()
    event_type = payload.get("type")
    data = payload.get("data", {})
    # Simulate logic to extract payment identifier and set status
    payment_id = data.get("object", {}).get("metadata", {}).get("payment_id")
    if not payment_id or payment_id not in payment_store:
        return JSONResponse(status_code=400, content={"message": "Invalid payment_id"})
    if event_type == "payment_intent.succeeded":
        payment_store[payment_id]["status"] = PaymentStatus.succeeded
    elif event_type == "payment_intent.payment_failed":
        payment_store[payment_id]["status"] = PaymentStatus.failed
    else:
        # Handle other cases as needed
        pass
    logging.info(f"Stripe webhook processed: {event_type} for {payment_id}")
    return {"message": "ok"}

# PUBLIC_INTERFACE
@app.post("/payments/events/fijian", tags=["integration"], summary="Fijian provider webhook endpoint", description="Webhook endpoint to receive events from the Fijian payment provider and update payment status accordingly.")
async def fijian_webhook(request: Request):
    """Handles payment events from the Fijian provider (simulate logic here)"""
    payload = await request.json()
    payment_id = payload.get("payment_id")
    status = payload.get("status")
    if not payment_id or payment_id not in payment_store:
        return JSONResponse(status_code=400, content={"message": "Invalid payment_id"})
    # In a real implementation, translate provider status to internal status
    if status == "success":
        payment_store[payment_id]["status"] = PaymentStatus.succeeded
    elif status == "failed":
        payment_store[payment_id]["status"] = PaymentStatus.failed
    elif status == "cancelled":
        payment_store[payment_id]["status"] = PaymentStatus.cancelled
    else:
        payment_store[payment_id]["status"] = PaymentStatus.pending
    logging.info(f"Fijian gateway webhook processed: {status} for {payment_id}")
    return {"message": "ok"}

# --- Mock Payment Processing (for DEMO only) ---
def mock_process_payment(payment_id: str, provider: PaymentProvider):
    import time
    import random
    # Simulate payment gateway processing delay
    time.sleep(2)
    # Randomly succeed/fail for demo
    if random.choice([True, False]):
        payment_store[payment_id]["status"] = PaymentStatus.succeeded
    else:
        payment_store[payment_id]["status"] = PaymentStatus.failed
    logging.info(f"Payment {payment_id} processed as {payment_store[payment_id]['status']}")

# PUBLIC_INTERFACE
@app.get("/payments/wsdoc", tags=["integration"], summary="WebSocket & Real-time Payment Integration Usage", description="Describes how to use websocket or webhook endpoints for real-time payment integration.")
async def wsdoc():
    """
    This endpoint describes how to integrate real-time payment status updates
    using webhook endpoints (Stripe/Fijian) or future websocket support for push notifications.
    """
    return {
        "stripe_webhook_info": "/payments/events/stripe (POST)",
        "fijian_webhook_info": "/payments/events/fijian (POST)",
        "note": "No websocket endpoint is enabled in this version. For real-time updates, rely on webhook notifications sent by providers."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
