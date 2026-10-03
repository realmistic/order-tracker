# Order Tracker

A small order tracking app for the AI Dev Tools Zoomcamp observability homework. It includes a web page, API, tests, and a Docker Compose setup. You add telemetry, alerts, and an incident responder in Homework 4.

The main user flow is creating an order and checking its status. Three sample orders are created on first startup.

## Run it

You need Docker with Compose. To run the tests, you also need Python 3.11+ and `uv`.

```bash
docker compose up --build -d --wait
```

Open <http://127.0.0.1:8000>. The API is at `/api/orders`, and the health check is at `/healthz`. Data is stored in a Docker volume and survives container recreation.

If port 8000 is occupied, set `ORDER_TRACKER_PORT`, for example:

```bash
ORDER_TRACKER_PORT=18080 docker compose up --build -d --wait
```

Run tests with `uv run --frozen pytest -q`. Stop the app with `docker compose down`. Add `-v` only if you also want to delete the order data.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Web page |
| GET | `/healthz` | Database health check |
| GET | `/api/orders` | List orders |
| POST | `/api/orders` | Create an order |
| GET | `/api/orders/{id}` | Check an order |
| PATCH | `/api/orders/{id}` | Change an order status |

The app uses SQLite to keep setup small. Run one app container at a time. The course exercise is about detecting and handling an incident, not scaling the database.

## Homework 4: DevOps and Observability Solutions

This repository includes complete solutions for all 6 homework questions:

### ✅ Q1: Run the app
- Started Order Tracker with `docker compose up`
- Health endpoint (`/healthz`) returns: `{"status": "ok"}`

### ✅ Q2: Instrument one endpoint
- Added OpenTelemetry instrumentation to FastAPI app
- Created custom console exporters for traces and metrics
- Order lookup (`/api/orders/standard-1001`) returns HTTP **200**
- Traces visible in Docker logs with full request metrics

### ✅ Q3: Build the telemetry pipeline
- Configured Prometheus for metrics collection
- Set up Grafana for dashboards and visualization
- Added OTel Collector for signal processing
- Order `standard-1002` returns HTTP **404** (Not Found)
- Complete stack: App → OTel Collector → Prometheus → Grafana

### ✅ Q4: Configure the alert - Answer: **Firing** 🔴
- Created Grafana alert rule for HTTP errors
- Configured with endpoint labels and time windows
- Alert linked to dashboard and documentation
- Alert state transitions to **Firing** when 5xx errors are triggered
- Webhook sends alert to incident responder for automatic analysis

### ✅ Q5: Build the incident responder - Answer: Claude's Analysis
**What Claude Returns:**
- Context analysis of alert severity, endpoint, and error patterns
- **Root cause hypothesis**: Data-format drift (ID format mismatch)
- **Ranked hypotheses**:
  1. Integer coercion bug (`int(order_id)` fails on `express-1002`)
  2. Route typed as integer (`<int:order_id>`)
  3. Naive ID splitting without bounds checking
  4. Write/read key mismatch between creation and lookup
  5. Missing not-found guard causing dereference of `None`
- **Triage commands**: Exact bash commands to confirm root cause
- **Remediation code**: Ready-to-apply Python fix treating IDs as opaque strings

Implementation:
- Created incident-response service on port 8001
- Accepts POST `/alerts` from Grafana webhooks
- Saves incident context (alerts, prompt, analysis) to disk
- Integrates Anthropic SDK to trigger Claude analysis
- API endpoints: `GET /incidents`, `GET /incidents/{id}`, `POST /alerts`

### ✅ Q6: Watch the agent fix the incident - Answer: **Data-Format Drift / Integer Coercion Bug**
**The Underlying Problem:**
- New order IDs use format: `express-1002`, `standard-1001` (string with prefix)
- Old code assumes numeric IDs: `int(order_id)`
- When `express-1002` is passed, `int()` throws `ValueError`
- Exception escapes handler as **HTTP 500** error

**Claude's Primary Diagnosis:**
This is a classic **data-format drift** bug: a new ID scheme was introduced at write time (order creation for express orders) without updating the read path.

**The Fix Claude Recommends:**
```python
def get_order(order_id: str):  # Keep as str, not int
    with connect() as db:
        row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:  # Explicit guard prevents dereference
        raise HTTPException(404, "Order not found")
    return order_detail(row)
```

**Complete Flow:**
1. ✅ Grafana alert fires when 5xx errors detected
2. ✅ Webhook sends alert to incident responder
3. ✅ Incident responder receives alert at `/alerts`
4. ✅ Claude analyzes the problem context
5. ✅ Claude identifies root cause and provides fix
6. ✅ Problem context and solution saved to disk

## Setup with Environment Variables

1. Copy the template:
```bash
cp .env-template .env
```

2. Add your Anthropic API key to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

3. Start the full stack:
```bash
docker compose up -d
```

4. Access services:
- **Order Tracker**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Incident Responder**: http://localhost:8001

## Testing the Incident Response Flow

Send a test alert to trigger Claude analysis:

```bash
curl -X POST http://localhost:8001/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "critical"
      },
      "annotations": {
        "description": "Test incident for Claude analysis"
      }
    }]
  }'
```

View saved incidents:
```bash
curl http://localhost:8001/incidents | jq .
```

## Key Features

- **OpenTelemetry Instrumentation**: Automatic tracing and metrics collection
- **Multi-backend Observability**: Prometheus for metrics, Grafana for visualization
- **AI-Powered Incident Response**: Claude analyzes alerts and provides remediation
- **Complete Docker Setup**: Everything runs in containers with proper networking
- **Secure Configuration**: API keys managed via `.env` file (not committed)
