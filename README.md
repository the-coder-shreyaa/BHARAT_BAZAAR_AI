# 🛍️ Bharat Bazaar AI

**Merchant-side AI Commerce Layer — Making your catalog AI-discoverable & AI-transactable**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-22%2F22%20Passed-brightgreen)](tests/)

### 🚀 ## 🚀 Live Demo

[🌐 Open Bharat Bazaar AI](https://bharatbazaarai-wehbsj6kdiqpsrciz9npd4.streamlit.app/)

---

## 🎯 Problem Statement

Traditional e-commerce websites are designed for human browsers. As AI shopping agents become prevalent, merchants need a way to make their catalogs **programmatically discoverable and transactable** by AI buyers — without rebuilding their entire stack.

## 💡 Solution

**Bharat Bazaar AI** provides an **agent-readable commerce protocol** — a structured API layer that sits on top of a merchant's catalog and enables any AI shopping agent to:

1. **Discover** the merchant's capabilities via `/.well-known/ai-commerce.json`
2. **Search** products with natural language and structured filters
3. **Inspect** product details and check stock
4. **Cart** items with validation
5. **Order** with server-side price calculation
6. **Pay** via Razorpay integration (or simulation mode)

All actions are logged in a secure **audit trail** for merchant transparency.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AI Shopping Agent                      │
│               (LLM-powered or Rule-based)                │
│                                                          │
│  NL Query → Tool Selection → API Calls → Result Chain    │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP (structured JSON)
┌────────────────────▼─────────────────────────────────────┐
│              FastAPI Commerce Layer                       │
│                                                          │
│  ┌─────────────┐ ┌──────────┐ ┌─────────────────────┐   │
│  │  Discovery   │ │ Commerce │ │  Dashboard Endpoints│   │
│  │  Manifest    │ │ 8 Tools  │ │  (orders, audit,    │   │
│  │  .well-known │ │  API     │ │   growth insights)  │   │
│  └─────────────┘ └──────────┘ └─────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Service Layer                        │    │
│  │  Catalog │ Cart │ Order │ Payment │ Audit │ Growth│    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              SQLite Database                      │    │
│  │  Products │ Carts │ Orders │ AuditLogs            │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│              Streamlit Merchant Dashboard                 │
│  Overview │ Catalog │ AI Demo │ Orders │ Growth │ Audit  │
└──────────────────────────────────────────────────────────┘
```

See [architecture.md](architecture.md) for detailed Mermaid diagrams.

---

## 🛠️ Agent-Readable Commerce Tools

| # | Tool | Method | Path | Purpose |
|---|------|--------|------|---------|
| 1 | `search_products` | POST | `/api/v1/tools/search_products` | Search by query, category, price, color, brand, size |
| 2 | `get_product` | GET | `/api/v1/tools/products/{id}` | Full product details |
| 3 | `check_stock` | GET | `/api/v1/tools/products/{id}/stock` | Availability + quantity |
| 4 | `create_cart` | POST | `/api/v1/tools/cart` | Create a new cart |
| 5 | `add_to_cart` | POST | `/api/v1/tools/cart/{id}/items` | Add product to cart |
| 6 | `create_order` | POST | `/api/v1/tools/orders` | Cart → Order (server-side pricing) |
| 7 | `get_order_status` | GET | `/api/v1/tools/orders/{id}` | Check order status |
| 8 | `create_checkout` | POST | `/api/v1/tools/orders/{id}/checkout` | Initiate Razorpay payment |

**Discovery:** `GET /.well-known/ai-commerce.json` — machine-readable manifest of all tools.

**Response Format:** Every endpoint returns:
```json
{
  "success": true|false,
  "data": { ... },
  "error": "message if failed",
  "tool": "tool_name"
}
```

---

## 📦 Catalog

32 realistic products across 4 categories:
- 👕 **Clothing** — Kurtis, shirts, sarees, t-shirts (Indian brands)
- 👟 **Shoes** — Sneakers, formal shoes, sandals, running shoes
- 💍 **Accessories** — Watches, sunglasses, wallets, belts
- 👜 **Bags** — Laptop bags, backpacks, totes, duffel bags

All products have:
- Prices in INR (₹)
- Realistic stock levels
- Structured attributes (color, material, brand, size)
- Cross-linked related products

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd bharat-bazaar-ai
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys (or leave defaults for simulation mode)
```

### 3. Start the API Server

```bash
python run.py
# → API running at http://localhost:8000
# → Swagger docs at http://localhost:8000/docs
# → Discovery manifest at http://localhost:8000/.well-known/ai-commerce.json
```

### 4. Start the Dashboard

```bash
streamlit run dashboard/app.py
# → Dashboard at http://localhost:8501
```

### 5. Run Tests

```bash
pytest tests/ -v
```

---

## 🤖 AI Buyer Agent

The AI buyer supports **two modes**:

### LLM-Powered Mode
Set `LLM_API_KEY` in `.env` for full natural language understanding via any OpenAI-compatible API.

### Rule-Based Fallback (Default)
Works without any API key using keyword extraction and regex:
- Detects: product type, color, price constraints, actions
- Supports Hindi-English mixed queries
- Example: *"Show me blue sneakers under 2000"* → search → select → stock check → cart → order → checkout

---

## 💳 Payment Integration

### Razorpay (Production)
Set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env` for real payment processing with Razorpay sandbox.

### Simulation Mode (Default)
When Razorpay keys are not configured, the system generates realistic simulated payment responses — no external calls made.

---

## 🔒 Security & Trust

- **Server-side price calculation** — order totals are always computed from the database, never from client input
- **Audit logging** — every agent tool call is logged with timestamps, session IDs, and sanitized inputs
- **Sensitive data redaction** — API keys, passwords, and secrets are automatically scrubbed from audit logs
- **Stock validation** — double-checked at cart addition and order creation
- **Duplicate order prevention** — same cart cannot generate multiple orders

---

## 📈 Growth Insights

The AI growth engine generates upsell/cross-sell recommendations from:
1. **Catalog relationships** — related products cross-linked in the seed data
2. **Co-purchase patterns** — products frequently ordered together

Each insight includes: recommended product, reason, target context, estimated additional value, and confidence score.

---

## 📁 Project Structure

```
bharat-bazaar-ai/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Settings from .env
│   ├── database.py             # SQLite engine + session
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── seed.py                 # 32 realistic products
│   ├── api/
│   │   ├── commerce.py         # 8 agent commerce tools + dashboard endpoints
│   │   └── discovery.py        # /.well-known/ai-commerce.json
│   ├── services/
│   │   ├── catalog.py          # Product search & lookup
│   │   ├── cart.py             # Cart management
│   │   ├── order.py            # Order creation & status
│   │   ├── payment.py          # Razorpay integration
│   │   ├── audit.py            # Audit log service
│   │   └── growth.py           # AI growth insights engine
│   └── agent/
│       ├── buyer.py            # AI buyer (LLM + rule-based fallback)
│       └── tools.py            # Tool registry → HTTP calls
├── dashboard/
│   ├── app.py                  # Streamlit 6-tab dashboard
│   └── components/
│       ├── overview.py         # Metrics & charts
│       ├── catalog.py          # Product browser
│       ├── ai_buyer_demo.py    # Interactive agent demo
│       ├── orders.py           # Order management
│       ├── growth_insights.py  # Upsell/cross-sell cards
│       └── audit_log.py        # Agent audit trail
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_catalog.py
│   ├── test_cart.py
│   ├── test_order.py
│   ├── test_payment.py
│   └── test_agent.py           # E2E agent flow
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── architecture.md
└── run.py
```

---

## 🏆 Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy ORM |
| Validation | Pydantic v2 |
| Dashboard | Streamlit |
| Payment | Razorpay (sandbox) |
| AI Agent | OpenAI-compatible LLM / Rule-based fallback |
| HTTP Client | HTTPX |
| Testing | Pytest + FastAPI TestClient |

---

## 📄 License

MIT License — built for the AI Growth & Agentic Commerce track.
