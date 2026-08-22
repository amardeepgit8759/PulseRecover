# 💳 Network-Resilient Payment Recovery Agent
> **Razorpay AI Buildathon – Track 03: AI Revenue Recovery**

An intelligent, policy-driven payment recovery agent built with **FastAPI**, **SQLAlchemy**, and **Background Tasks**. It automatically attributes payment failure root causes (such as bank network timeouts vs user cancellations) and executes automated, risk-bounded retry policies to maximize payment recovery rates.

---

## 🌟 Key Features

- **🔍 Heuristic Failure Attribution**: Categorizes transaction failures (`network`, `bank`, `user`, `gateway`) using error codes, failure messages, and latency signals (`time_taken_ms`).
- **🛡️ Policy-Driven Recovery**: Enforces safety guardrails before triggering auto-retries:
  - Max 3 retries per transaction.
  - ₹5,000 auto-retry limit.
  - Allowed payment methods (`upi`, `card`).
  - Staggered retry delays (`30s`, `120s`, `300s`).
  - 2-hour maximum recovery window.
- **⚡ Asynchronous Background Tasks**: Non-blocking failure processing and background retry orchestration using FastAPI `BackgroundTasks`.
- **📊 Real-time Recovery Analytics**: Comprehensive audit trails (`/orders/{id}/audit`) and overall recovery rate stats (`/stats`).

---

## 🏗️ Project Structure

```
network-recovery-agent/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── policy.py      # Recovery policy rules & limits
│   │   │   └── tools.py       # Failure attribution & decision engine
│   │   ├── database.py        # Database session & engine setup
│   │   ├── main.py            # FastAPI routes & background task handlers
│   │   └── models.py          # SQLAlchemy ORM models
│   ├── .env.example
│   ├── requirements.txt
│   └── recovery_agent.db
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
python -m uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`. Direct your browser to `http://127.0.0.1:8000/docs` to test endpoints via Swagger UI.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Project details & version status |
| `GET` | `/health` | Server health check |
| `POST` | `/orders` | Create a new payment order |
| `POST` | `/simulate/network-failure` | Simulate payment failure & trigger agent recovery |
| `GET` | `/orders` | List latest payment orders |
| `GET` | `/orders/{order_id}/audit` | View detailed audit trail for an order |
| `GET` | `/stats` | View real-time recovery metrics & recovery rate % |

---

## 🐙 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/network-recovery-agent.git
git branch -M main
git push -u origin main
```
