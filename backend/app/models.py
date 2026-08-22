from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    razorpay_order_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, default="created")  # created, failed, recovered, deferred
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("PaymentAttempt", back_populates="order", cascade="all, delete-orphan")
    failures = relationship("FailureEvent", back_populates="order", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="order", cascade="all, delete-orphan")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    razorpay_payment_id = Column(String, nullable=False)
    method = Column(String, default="upi")
    status = Column(String, default="failed")
    error_code = Column(String, nullable=True)
    error_description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="attempts")


class FailureEvent(Base):
    __tablename__ = "failure_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    attributed_cause = Column(String, nullable=False)  # network, bank, user, gateway
    confidence = Column(Float, default=0.0)
    signals = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="failures")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    action = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    policy_applied = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="audit_logs")
