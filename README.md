# PulseRecover – Network-Resilient Payment Recovery Agent

** AI Revenue Recovery**

> An intelligent payment recovery agent that detects network-related payment failures, attributes root causes, and executes **policy-bounded** recovery actions — with full auditability and graceful failure handling.

---

## The Problem

According to a LocalCircles survey (August 2026):

- **83%** of digital payment users in India face at least one disruption every month due to poor mobile networks
- **37%** of users lose more than 20% of their monthly transactions
- Most of these failures are silent and lead to **revenue leakage** for merchants

Traditional retry systems treat all failures the same. They don’t understand *why* a payment failed.

---

## The Solution

**PulseRecover** is a network-aware AI recovery agent that:

1. Detects payment failures
2. Attributes the root cause (`network`, `bank`, `user`, `gateway`)
3. Applies **hard policy rules** before taking any action
4. Executes bounded recovery (retry / create recovery link / stop gracefully)
5. Maintains a complete **immutable audit trail**

Every money-related decision is **explainable, bounded, and gated**.

---

## Why This Project is Unique

| Feature | How PulseRecover handles it |
|--------|-----------------------------|
| Network-aware attribution | Uses error codes + latency signals (`time_taken_ms`) |
| Hard policy engine | Max retries, amount limits, time windows |
| Graceful failure | Creates recovery link even when auto-retry is blocked |
| Full auditability | Every decision is logged with reason + policy applied |
| Measurable impact | Real-time recovery rate via `/stats` |

---

## The Razorpay Bar

This project is designed to meet the evaluation criteria:

- Every money action is **explainable**
- Actions are **bounded and gated** by policy
- Full **audit trail** is available
- One failure is handled **gracefully**

---

## Architecture
Payment Failure
↓
Attribute Cause (network / bank / user / gateway)
↓
Policy Engine (hard rules)
↓
Decision
├── Retry Scheduled + Recovery Link
└── Stop Gracefully + Recovery Link
↓
Immutable Audit Log
↓
Recovery Stats
text---

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLAlchemy + SQLite
- **Agent**: Rule-based decision engine + policy gates
- **Payments**: Razorpay-compatible (mock + test mode ready)
- **Async**: FastAPI BackgroundTasks

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/amardeepgit8759/PulseRecover.git
cd PulseRecover/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload
Open: http://127.0.0.1:8000/docs

API Endpoints













































MethodEndpointDescriptionGET/Project infoGET/healthHealth checkPOST/ordersCreate a new orderPOST/simulate/network-failureSimulate network failure & trigger agentGET/ordersList ordersGET/orders/{id}/auditFull audit trail of decisionsGET/statsRecovery rate & metrics

Demo Flow

Create an order

JSONPOST /orders
{
  "amount": 499,
  "customer_email": "test@example.com"
}

Simulate a network failure

JSONPOST /simulate/network-failure
{
  "order_id": 1,
  "error_code": "GATEWAY_TIMEOUT",
  "error_description": "Network timeout while contacting bank",
  "time_taken_ms": 18000
}

Check the audit trail

textGET /orders/1/audit

View recovery stats

textGET /stats

Sample Audit Trail
JSON[
  {
    "action": "create_order",
    "reason": "Order created via API"
  },
  {
    "action": "attribute",
    "reason": "Attributed as 'network' with confidence 0.85"
  },
  {
    "action": "create_recovery_link",
    "reason": "Created recovery payment link for amount ₹499.0"
  },
  {
    "action": "retry_scheduled",
    "reason": "Policy passed. Scheduling retry after 120s. Recovery link also created."
  }
]

Policy Rules (Hard Gates)

Maximum 3 retries
Auto-retry only if amount ≤ ₹5,000
Only network failures are auto-retried
Confidence must be ≥ 0.6
Recovery window: 2 hours
Allowed methods: upi, card


Project Structure
textPulseRecover/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── policy.py      # Hard policy rules
│   │   │   └── tools.py       # Attribution + decision engine
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
└── README.md

Future Improvements

Real Razorpay Payment Links integration
LLM-based richer failure attribution
WhatsApp / SMS recovery notifications
Multi-merchant anonymized failure signals
Dashboard UI for merchants


Author
Amardeep Kumar

GitHub: amardeepgit8759

License
This project was built for the Razorpay AI Buildathon 2026.
text---

### How to update it on GitHub:

1. Go to your repository: https://github.com/amardeepgit8759/PulseRecover
2. Click on `README.md`
3. Click the pencil icon (Edit)
4. Delete the old content
5. Paste the new content above
6. Click **Commit changes**

---

After you update it, reply **“README updated”** and I will give you the **Demo / Pitch
