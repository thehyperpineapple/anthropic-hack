# OrderFlow AI

An AI-powered order management platform for wholesale food distributors. Employees can submit orders via voice or text, and the system uses Anthropic Claude to extract structured order data, detect anomalies, and generate customer quotes — all through a modern web interface.

## Features

### Order Processing
- **Voice Orders** — Record audio directly in the browser with real-time transcription powered by ElevenLabs Scribe
- **Text Orders** — Type, paste, or upload order files (.txt, .pdf, .docx, .csv)
- **AI Extraction** — Claude parses unstructured order messages into structured line items with SKUs, quantities, and prices
- **Anomaly Detection** — Automatically flags unusually large orders or suspicious patterns for human review

### Dashboard
- **Order Management** — View, filter, and search all orders with status tracking (Processing, Review, Completed, Error)
- **Approve / Reject** — One-click review workflow for flagged orders
- **Analytics** — Revenue charts, order status breakdown, top products, and customer insights
- **Client & Employee Views** — Toggle between employee-wide and per-client analytics

### General
- **Dark Mode** — Full dark/light theme support
- **Responsive UI** — Modern interface built with Next.js, Tailwind CSS, and Framer Motion
- **Real-time Data** — Frontend pulls live data from the FastAPI backend

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic |
| Database | PostgreSQL (Neon) via asyncpg |
| AI | Anthropic Claude (order parsing & extraction) |
| Transcription | ElevenLabs Scribe (real-time voice-to-text) |
| Deployment | Local development with Uvicorn + Next.js dev server |

## Architecture

```
┌─────────────────────────────────────────┐
│              Next.js Frontend            │
│  ┌──────────┐ ┌───────────┐ ┌─────────┐ │
│  │  Upload   │ │ Dashboard │ │  Navbar │ │
│  │ (voice/   │ │ (orders,  │ │ (theme, │ │
│  │  text)    │ │ analytics)│ │  nav)   │ │
│  └─────┬─────┘ └─────┬─────┘ └─────────┘ │
│        │              │                    │
│        └──────┬───────┘                    │
│               ▼                            │
│     /api/scribe-token (ElevenLabs)        │
└───────────────┬────────────────────────────┘
                │ HTTP
                ▼
┌─────────────────────────────────────────┐
│            FastAPI Backend               │
│                                          │
│  /customers  /orders  /analytics         │
│  /inventory  /orders/process             │
│               │                          │
│       ┌───────┴────────┐                 │
│       ▼                ▼                 │
│  OrderProcessor   AnomalyService         │
│  (Claude AI)      (flagging logic)       │
│       │                                  │
│       ▼                                  │
│   PostgreSQL (Neon)                      │
└──────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.11+ with Conda
- Node.js 18+
- PostgreSQL database (or a Neon account)

### 1. Clone the Repository

```bash
git clone https://github.com/pxndey/anthropic-hack.git
cd anthropic-hack
```

### 2. Backend Setup

```bash
cd backend

# Create and activate conda environment
conda create -n anthropic python=3.11
conda activate anthropic

# Install dependencies
pip install -r requirements.txt
```

Create a `backend/.env` file:

```env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?ssl=require
```

Start the backend:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000` with docs at `/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
npm run dev # for dev 
npm run build # for build
```

Create a `frontend/.env` file with the following variables:

```env
# Required — same Anthropic key used by the backend
ANTHROPIC_API_KEY=sk-ant-...

# Required — same Neon/PostgreSQL connection string as the backend
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?ssl=require

# Required — powers real-time voice transcription (ElevenLabs Scribe)
ELEVENLABS_API_KEY=sk_...

# Optional — Bland AI agent integration
BL_WORKSPACE=your-workspace
BL_API_KEY=bl_...
BL_AGENT_NAME=your-agent

# Optional — override the backend URL (defaults to http://localhost:8000)
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

#### Frontend Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with Turbopack |
| `npm run build` | Create production build |
| `npm run start` | Run production server |
| `npm run lint` | Run ESLint |

#### Key Frontend Dependencies

- **Next.js 16** — App Router with Turbopack
- **React 19** — UI library
- **Tailwind CSS 3** — Utility-first styling
- **shadcn/ui** — Accessible component primitives (Radix UI under the hood)
- **Framer Motion** — Page transitions and micro-animations
- **Recharts** — Dashboard analytics charts
- **@elevenlabs/react** — Real-time voice transcription via ElevenLabs Scribe
- **next-themes** — Dark / light mode support

## API Endpoints

### Customers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers` | List all customers |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | List orders (filter by `customer_id`, `status_filter`) |
| GET | `/orders/{order_id}` | Get order details |
| POST | `/orders/process` | Process a new order from text/voice transcript |
| PATCH | `/orders/{order_id}/status` | Update order status (approve/reject) |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/summary` | Revenue, order counts, status breakdown |
| GET | `/analytics/top-products` | Top products by quantity/revenue |

### Inventory
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory` | List all inventory items |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Project Structure

```
anthropic-hack/
├── backend/
│   ├── main.py                    # FastAPI app & router registration
│   ├── config.py                  # Settings & environment validation
│   ├── database.py                # SQLAlchemy async engine setup
│   ├── dependencies.py            # FastAPI dependency injection
│   ├── models.py                  # ORM models (Customer, Order, Inventory)
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── seed.py                    # Database seeding script
│   ├── requirements.txt           # Python dependencies
│   ├── routers/
│   │   ├── customers.py           # Customer endpoints
│   │   ├── orders.py              # Order CRUD + AI processing
│   │   ├── analytics.py           # Analytics & reporting
│   │   └── inventory.py           # Inventory management
│   └── services/
│       ├── ai_service.py          # Anthropic Claude integration
│       ├── order_processor.py     # Order parsing pipeline
│       ├── order_orchestrator.py  # End-to-end processing flow
│       └── anomaly_service.py     # Anomaly detection logic
│
└── frontend/
    ├── app/
    │   ├── layout.tsx             # Root layout with theme provider
    │   ├── page.tsx               # Root redirect → /upload
    │   ├── globals.css            # Global styles + dark mode variables
    │   ├── upload/page.tsx        # Voice & text order submission
    │   ├── dashboard/page.tsx     # Order management & analytics
    │   └── api/
    │       └── scribe-token/      # ElevenLabs token proxy
    ├── components/
    │   ├── navbar.tsx             # Top navigation bar
    │   ├── order-detail-panel.tsx # Slide-over order details + approve/reject
    │   ├── orders-table.tsx       # Sortable orders table
    │   ├── stats-cards.tsx        # Dashboard stat cards
    │   ├── client-analytics.tsx   # Per-client charts
    │   ├── employee-analytics.tsx # Employee-wide charts
    │   ├── status-badge.tsx       # Order status badges
    │   ├── theme-provider.tsx     # Dark/light mode provider
    │   └── ui/                    # shadcn/ui component library
    └── lib/
        ├── api.ts                 # Backend API client
        ├── data.ts                # Types, mock data, utilities
        └── dashboard-utils.ts     # Analytics computation helpers
```

## License

Anthropic Hackathon Project
