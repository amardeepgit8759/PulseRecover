from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from .database import engine, Base, get_db
from . import models
from .agent.tools import attribute_failure, decide_and_act, get_failure_details

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Network-Resilient Payment Recovery Agent",
    description="Razorpay AI Buildathon – Track 03",
    version="0.2.0"
)


class CreateOrderRequest(BaseModel):
    amount: float
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


class SimulateFailureRequest(BaseModel):
    order_id: int
    error_code: str = "GATEWAY_TIMEOUT"
    error_description: str = "Network timeout while contacting bank"
    time_taken_ms: int = 18000


@app.get("/")
def root():
    return {
        "project": "Network-Resilient Payment Recovery Agent",
        "track": "03 - AI Revenue Recovery",
        "version": "0.2.0",
        "status": "Phase 2"
    }


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/orders")
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    order = models.Order(
        razorpay_order_id=f"order_mock_{uuid.uuid4().hex[:12]}",
        amount=payload.amount,
        currency="INR",
        status="created",
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    audit = models.AuditLog(
        order_id=order.id,
        action="create_order",
        reason="Order created via API",
        policy_applied=None
    )
    db.add(audit)
    db.commit()

    return {
        "id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": order.amount,
        "status": order.status
    }


@app.post("/simulate/network-failure")
def simulate_network_failure(
    payload: SimulateFailureRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    attempt = models.PaymentAttempt(
        order_id=order.id,
        razorpay_payment_id=f"pay_mock_{uuid.uuid4().hex[:10]}",
        method="upi",
        status="failed",
        error_code=payload.error_code,
        error_description=payload.error_description
    )
    db.add(attempt)
    order.status = "failed"
    db.commit()
    db.refresh(attempt)

    def run_recovery(order_id: int):
        from .database import SessionLocal
        local_db = SessionLocal()
        try:
            signals = {
                "error_code": payload.error_code,
                "error_description": payload.error_description,
                "time_taken_ms": payload.time_taken_ms
            }
            attribute_failure(local_db, order_id, signals)
            decide_and_act(local_db, order_id)
        finally:
            local_db.close()

    background_tasks.add_task(run_recovery, order.id)

    return {
        "message": "Network failure simulated. Recovery agent triggered.",
        "order_id": order.id,
        "attempt_id": attempt.id
    }


@app.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).limit(20).all()
    return [
        {
            "id": o.id,
            "razorpay_order_id": o.razorpay_order_id,
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at
        }
        for o in orders
    ]


@app.get("/orders/{order_id}/audit")
def get_audit_trail(order_id: int, db: Session = Depends(get_db)):
    logs = db.query(models.AuditLog).filter(models.AuditLog.order_id == order_id).order_by(models.AuditLog.created_at).all()
    return [
        {
            "action": log.action,
            "reason": log.reason,
            "policy_applied": log.policy_applied,
            "created_at": log.created_at
        }
        for log in logs
    ]


@app.get("/stats")
def recovery_stats(db: Session = Depends(get_db)):
    total = db.query(models.Order).count()
    failed = db.query(models.Order).filter(models.Order.status.in_(["failed", "recovered", "deferred"])).count()
    recovered = db.query(models.Order).filter(models.Order.status == "recovered").count()
    deferred = db.query(models.Order).filter(models.Order.status == "deferred").count()
    rate = round((recovered / failed * 100), 1) if failed > 0 else 0

    return {
        "total_orders": total,
        "failed_or_processed": failed,
        "recovered": recovered,
        "deferred": deferred,
        "recovery_rate_percent": rate
    }