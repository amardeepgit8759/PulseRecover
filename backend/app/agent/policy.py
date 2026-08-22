from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class PolicyConfig:
    max_retries: int = 3
    max_amount_auto_retry: float = 5000.0
    allowed_methods: List[str] = None
    retry_delays_seconds: List[int] = None
    stop_after_hours: int = 2

    def __post_init__(self):
        if self.allowed_methods is None:
            self.allowed_methods = ["upi", "card"]
        if self.retry_delays_seconds is None:
            self.retry_delays_seconds = [30, 120, 300]


DEFAULT_POLICY = PolicyConfig()


def can_retry(
    amount: float,
    current_retry_count: int,
    attributed_cause: str,
    confidence: float,
    first_attempt_time: datetime,
    method: Optional[str] = None,
    policy: PolicyConfig = DEFAULT_POLICY
) -> tuple[bool, str]:
    if current_retry_count >= policy.max_retries:
        return False, f"Max retries ({policy.max_retries}) already reached"

    if amount > policy.max_amount_auto_retry:
        return False, f"Amount ₹{amount} exceeds auto-retry limit of ₹{policy.max_amount_auto_retry}"

    if attributed_cause != "network":
        return False, f"Only network failures are auto-retried. Cause was: {attributed_cause}"

    if confidence < 0.6:
        return False, f"Attribution confidence too low ({confidence:.2f} < 0.6)"

    hours_elapsed = (datetime.utcnow() - first_attempt_time).total_seconds() / 3600
    if hours_elapsed > policy.stop_after_hours:
        return False, f"Recovery window of {policy.stop_after_hours} hours has expired"

    if method and method not in policy.allowed_methods:
        return False, f"Method '{method}' is not in allowed list: {policy.allowed_methods}"

    return True, "All policy checks passed"


def get_next_retry_delay(current_retry_count: int, policy: PolicyConfig = DEFAULT_POLICY) -> int:
    if current_retry_count < len(policy.retry_delays_seconds):
        return policy.retry_delays_seconds[current_retry_count]
    return policy.retry_delays_seconds[-1]