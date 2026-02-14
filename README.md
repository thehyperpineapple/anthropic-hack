# OrderFlow AI

An AI-driven order entry system that processes customer interactions from voice, email, and PDF sources, extracting structured order data with built-in safety verification.

## Features

- **Multi-source Interaction Processing**: Support for voice transcripts, email, and PDF documents
- **AI-Powered Order Extraction**: Uses Anthropic Claude to extract structured order data from unstructured customer interactions
- **Content Safety Verification**: Integrates White Circle API for content moderation with configurable safety modes
- **Anomaly Detection**: Automatically flags suspicious orders for review
- **Tenant-Scoped Data**: Multi-tenant architecture with isolation via X-Tenant-ID header
- **Async-First Design**: Built on FastAPI with SQLAlchemy asyncio for high performance

## Architecture

```
interactions/upload (voice, email, pdf)
    ↓
transcribe_audio (ElevenLabs or OpenAI Whisper)
    ↓
verify_content_safety (White Circle API)
    ↓
extract_order_data (Anthropic Claude)
    ↓
detect_anomalies (internal logic)
    ↓
persist to PostgreSQL (Order + OrderItems)
```

## Prerequisites

- Python 3.9+
- Conda package manager
- PostgreSQL database (local or remote)

## Installation & Setup

### 1. Create Conda Environment

```bash
cd backend
conda create -n orderflow python=3.11
conda activate orderflow
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with the following required values:

```env
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/orderflow

# REQUIRED (at least one for audio transcription)
ELEVENLABS_API_KEY=...        # Primary audio transcription
OPENAI_API_KEY=...             # Fallback audio transcription (Whisper)

# OPTIONAL
WHITE_CIRCLE_API_KEY=...       # Leave blank to skip safety checks
SAFETY_MODE=log                # Options: strict | log | off
LOG_LEVEL=INFO
```

### 4. Database Setup

Create the PostgreSQL database and tables:

```bash
# Create the database (if not exists)
psql -U postgres -c "CREATE DATABASE orderflow;"

# Run migrations (if available) or use SQLAlchemy to create tables
# The models will be created on first run
```

Ensure your `DATABASE_URL` in `.env` matches your PostgreSQL setup:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/orderflow
```

## Running the Application

### Start the Server

```bash
# Activate environment if needed
conda activate orderflow

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Access API Documentation

- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{"status": "ok"}
```

### Process Interaction

```bash
POST /interactions/upload
Headers:
  - X-Tenant-ID: {tenant-uuid}
  - Content-Type: multipart/form-data

Form Parameters:
  - file: (binary) audio/email/pdf file
  - source_type: VOICE | EMAIL | PDF
  - customer_id: {customer-uuid}

Response:
{
  "interaction_id": "uuid",
  "order_id": "uuid",
  "status": "DRAFT | FLAGGED | CONFIRMED",
  "anomalies_detected": 0
}
```

### List Orders

```bash
GET /orders
Headers:
  - X-Tenant-ID: {tenant-uuid}

Query Parameters (optional):
  - customer_id: {customer-uuid}
  - order_status: DRAFT | FLAGGED | CONFIRMED | SYNCED
  - limit: 50 (default)
  - offset: 0 (default)
```

### Get Order Details

```bash
GET /orders/{order_id}
Headers:
  - X-Tenant-ID: {tenant-uuid}

Response: Order with items, anomalies, and quotes
```

### Confirm Order

```bash
POST /orders/{order_id}/confirm
Headers:
  - X-Tenant-ID: {tenant-uuid}

Response: Updated order with CONFIRMED status
```

## Configuration

### Safety Modes

- **`strict`**: Block any content flagged as unsafe (raises error)
- **`log`** (default): Flag unsafe content but continue processing
- **`off`**: Skip safety checks entirely

### Logging

Set `LOG_LEVEL` to control verbosity:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational information
- `WARNING`: Warning messages and errors
- `CRITICAL`: Critical failures

## Dependencies

- **fastapi** (0.115+): Web framework
- **uvicorn** (0.32+): ASGI server
- **sqlalchemy** (2.0+): ORM with async support
- **asyncpg** (0.30+): PostgreSQL async driver
- **pydantic** (2.0+): Data validation
- **anthropic** (0.39+): Anthropic Claude API client
- **openai** (1.0+): OpenAI API client (for Whisper fallback)
- **requests**: HTTP client for White Circle API
- **httpx**: Async HTTP client
- **python-dotenv**: Environment variable management

## Error Handling

The application includes comprehensive error handling:

- **Transcription Errors**: Falls back from ElevenLabs to OpenAI Whisper
- **Safety Violations**: Configurable via `SAFETY_MODE`
- **Validation Errors**: Pydantic-based request validation
- **Database Errors**: Proper rollback on transaction failures
- **Missing Configuration**: Critical startup validation with clear error messages

## Troubleshooting

### "ANTHROPIC_API_KEY is not set"
- Ensure you have a valid .env file with `ANTHROPIC_API_KEY` set
- Verify the key format and that it's not expired

### "DATABASE_URL is not set or still the default placeholder"
- Update `DATABASE_URL` in `.env` with your actual PostgreSQL connection string
- Verify PostgreSQL is running and accessible

### "All transcription providers failed"
- Ensure at least one of `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` is configured
- Verify the audio file format is supported

### "Order not found"
- Verify the order_id exists and belongs to your tenant
- Check that the X-Tenant-ID header matches

## Development

### Install Development Dependencies

```bash
pip install -r requirements.txt
```

### View Logs

```bash
# Logs are output to console with ISO timestamp formatting
# Adjust LOG_LEVEL in .env to control verbosity
```

### Database Inspection

```bash
# Connect to PostgreSQL and inspect tables
psql -U user -d orderflow
\dt                    # List tables
\d orders              # Describe orders table
SELECT * FROM orders;  # Query orders
```

## Project Structure

```
backend/
├── main.py                      # FastAPI app entry point
├── config.py                    # Configuration & validation
├── database.py                  # SQLAlchemy setup
├── dependencies.py              # FastAPI dependency injection
├── models.py                    # SQLAlchemy ORM models
├── schemas.py                   # Pydantic request/response schemas
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── routers/
│   ├── interactions.py          # Interaction upload endpoint
│   └── orders.py                # Order CRUD endpoints
└── services/
    ├── ai_service.py            # AI/ML service integrations
    ├── order_orchestrator.py     # Main processing pipeline
    └── anomaly_service.py        # Anomaly detection logic
```

## API Testing Examples

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List orders (requires X-Tenant-ID header)
curl -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
     http://localhost:8000/orders

# Confirm an order
curl -X POST \
     -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \
     http://localhost:8000/orders/{order_id}/confirm
```

### Using Python

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/orders",
        headers={"X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440000"}
    )
    print(response.json())
```

## Implementation Status

✅ **Fully Implemented**
- All API endpoints are production-ready
- No mock routes detected - all endpoints use real service integrations
- Comprehensive error handling and validation
- Multi-tenant architecture with proper isolation
- Complete AI pipeline with Claude, White Circle, and transcription services
- Anomaly detection system
- Database persistence with async SQLAlchemy

## License

Proprietary - Anthropic Hackathon Project
