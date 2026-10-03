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

### ✅ Q4: Configure the alert
- Created Grafana alert rule for HTTP errors
- Configured with endpoint labels and time windows
- Alert linked to dashboard and documentation

### ✅ Q5: Build the incident responder
- Created incident-response service on port 8001
- Accepts POST `/alerts` from Grafana webhooks
- Saves incident context (alerts, analysis) to disk
- Integrates Anthropic SDK for automatic Claude analysis
- API endpoints: `GET /incidents`, `GET /incidents/{id}`, `POST /alerts`

### ✅ Q6: Watch the agent fix the incident
- Webhook connects Grafana alerts to incident responder
- Claude analyzes incidents automatically
- Provides root cause analysis and remediation suggestions

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
