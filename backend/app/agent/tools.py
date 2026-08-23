from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from .. import models
from .policy import can_retry, get_next_retry_delay, DEFAULT_POLICY


def get_failure_details(db: Session, order_id: int) -> Dict[str, Any]:
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}

    latest_failure = (
        db.query(models.FailureEvent)
        .filter(models.FailureEvent.order_id == order_id)
        .order_by(models.FailureEvent.created_at.desc())
        .first()
    )

    attempts = db.query(models.PaymentAttempt).filter(models.PaymentAttempt.order_id == order_id).all()

    return {
        "order_id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "amount": order.amount,
        "status": order.status,
        "attempt_count": len(attempts),
        "latest_cause": latest_failure.attributed_cause if latest_failure else None,
        "confidence": latest_failure.confidence if latest_failure else 0.0,
        "created_at": order.created_at.isoformat() if order.created_at else None
    }


def attribute_failure(db: Session, order_id: int, signals: Optional[Dict] = None) -> Dict[str, Any]:
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}

    cause = "unknown"
    confidence = 0.4

    if signals:
        error_code = str(signals.get("error_code", "")).lower()
        error_desc = str(signals.get("error_description", "")).lower()
        time_taken = signals.get("time_taken_ms", 0)

        network_keywords = ["timeout", "network", "connection", "unreachable", "gateway timeout", "503", "504"]
        bank_keywords = ["insufficient", "declined by bank", "do not honour", "invalid account"]
        user_keywords = ["cancelled", "user aborted", "incorrect pin"]

        if any(k in error_code or k in error_desc for k in network_keywords) or time_taken > 15000:
            cause = "network"
            confidence = 0.85
        elif any(k in error_code or k in error_desc for k in bank_keywords):
            cause = "bank"
            confidence = 0.8
        elif any(k in error_code or k in error_desc for k in user_keywords):
            cause = "user"
            confidence = 0.9
        else:
            cause = "gateway"
            confidence = 0.6

    failure = models.FailureEvent(
        order_id=order_id,
        attributed_cause=cause,
        confidence=confidence,
        signals=signals or {}
    )
    db.add(failure)

    audit = models.AuditLog(
        order_id=order_id,
        action="attribute",
        reason=f"Attributed as '{cause}' with confidence {confidence:.2f}",
        policy_applied="rule_based_v1",
        metadata_={"signals": signals}
    )
    db.add(audit)
    db.commit()

    return {
        "order_id": order_id,
        "attributed_cause": cause,
        "confidence": confidence
    }


def create_recovery_link(db: Session, order_id: int) -> Dict[str, Any]:
    """
    Create a mock recovery payment link.
    In real project this would call Razorpay Payment Links API.
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}

    recovery_link_id = f"plink_mock_{uuid.uuid4().hex[:10]}"
    recovery_url = f"https://rzp.io/i/{recovery_link_id}"

    audit = models.AuditLog(
        order_id=order_id,
        action="create_recovery_link",
        reason=f"Created recovery payment link for amount ₹{order.amount}",
        policy_applied="default_policy",
        metadata_={
            "recovery_link_id": recovery_link_id,
            "recovery_url": recovery_url,
            "amount": order.amount
        }
    )
    db.add(audit)
    db.commit()

    return {
        "recovery_link_id": recovery_link_id,
        "recovery_url": recovery_url,
        "amount": order.amount
    }


def decide_and_act(db: Session, order_id: int) -> Dict[str, Any]:
    details = get_failure_details(db, order_id)
    if "error" in details:
        return details

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    attempts = db.query(models.PaymentAttempt).filter(models.PaymentAttempt.order_id == order_id).count()

    allowed, reason = can_retry(
        amount=order.amount,
        current_retry_count=attempts,
        attributed_cause=details.get("latest_cause") or "unknown",
        confidence=details.get("confidence") or 0.0,
        first_attempt_time=order.created_at
    )

    # ---------- GRACEFUL STOP ----------
    if not allowed:
        order.status = "deferred"

        # Still create a recovery link so merchant can recover manually later
        link_info = create_recovery_link(db, order_id)

        audit = models.AuditLog(
            order_id=order_id,
            action="stop_gracefully",
            reason=reason,
            policy_applied="default_policy",
            metadata_={
                "recovery_url": link_info.get("recovery_url"),
                "message": "Auto-recovery stopped. Recovery link created for manual follow-up."
            }
        )
        db.add(audit)
        db.commit()

        return {
            "action": "stop_gracefully",
            "reason": reason,
            "status": "deferred",
            "recovery_url": link_info.get("recovery_url"),
            "message": "Policy blocked auto-retry. Recovery link created for merchant."
        }

    # ---------- RECOVERY PATH ----------
    delay = get_next_retry_delay(attempts)
    link_info = create_recovery_link(db, order_id)

    audit = models.AuditLog(
        order_id=order_id,
        action="retry_scheduled",
        reason=f"Policy passed. Scheduling retry after {delay}s. Recovery link also created.",
        policy_applied="default_policy",
        metadata_={
            "delay_seconds": delay,
            "attempt_number": attempts + 1,
            "recovery_url": link_info.get("recovery_url")
        }
    )
    db.add(audit)

    order.status = "recovered"
    db.commit()

    return {
        "action": "retry_scheduled",
        "delay_seconds": delay,
        "attempt_number": attempts + 1,
        "recovery_url": link_info.get("recovery_url"),
        "reason": "Policy checks passed",
        "status": "recovered"
    }