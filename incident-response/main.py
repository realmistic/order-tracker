import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from anthropic import Anthropic

app = FastAPI(title="Incident Responder")

INCIDENTS_DIR = Path("/tmp/incidents")
INCIDENTS_DIR.mkdir(exist_ok=True)


class AlertMessage(BaseModel):
    status: str
    alerts: list
    groupLabels: Optional[dict] = None
    commonLabels: Optional[dict] = None
    commonAnnotations: Optional[dict] = None
    externalURL: Optional[str] = None
    version: str = "4"
    groupKey: Optional[str] = None


@app.post("/alerts")
async def receive_alert(alert: AlertMessage):
    """Receive Grafana alerts and trigger incident response."""

    # Save alert context
    incident_id = datetime.now().isoformat().replace(":", "-")
    incident_dir = INCIDENTS_DIR / incident_id
    incident_dir.mkdir(exist_ok=True)

    # Save the alert data
    alert_file = incident_dir / "alert.json"
    with open(alert_file, "w") as f:
        json.dump(alert.dict(), f, indent=2)

    print(f"[INCIDENT] Received alert: {alert.status}")
    print(f"[INCIDENT] Alert data saved to {alert_file}")

    # Extract problem context from the alert
    problem_description = "Grafana Alert Fired"
    if alert.alerts:
        first_alert = alert.alerts[0]
        if isinstance(first_alert, dict):
            if "annotations" in first_alert and "description" in first_alert["annotations"]:
                problem_description = first_alert["annotations"]["description"]
            if "labels" in first_alert and "severity" in first_alert["labels"]:
                problem_description += f" (Severity: {first_alert['labels']['severity']})"

    # Create a prompt for the AI agent
    prompt = f"""
An incident has been triggered: {problem_description}

Alert Details:
{json.dumps(alert.dict(), indent=2)}

Please analyze this alert and determine:
1. What is the underlying problem?
2. What code or configuration change would fix it?
3. Provide the fix.

Context: This is an Order Tracker application that manages order creation and status checks.
"""

    # Save the prompt
    prompt_file = incident_dir / "prompt.txt"
    with open(prompt_file, "w") as f:
        f.write(prompt)

    # Invoke the coding agent in headless mode using Anthropic SDK
    print(f"[INCIDENT] Triggering AI agent for incident {incident_id}")

    agent_response = ""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            agent_response = "No ANTHROPIC_API_KEY environment variable set"
        else:
            client = Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-opus-5",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            agent_response = message.content[0].text

    except Exception as e:
        agent_response = f"Error invoking agent: {str(e)}"
        print(f"[INCIDENT] Agent error: {e}")

    # Save the agent response
    response_file = incident_dir / "response.txt"
    with open(response_file, "w") as f:
        f.write(agent_response)

    print(f"[INCIDENT] Agent response saved to {response_file}")
    print(f"[INCIDENT] Agent response preview:\n{agent_response[:500]}...")

    return {
        "status": "acknowledged",
        "incident_id": incident_id,
        "incident_dir": str(incident_dir),
        "agent_response_preview": agent_response[:200] + "..." if len(agent_response) > 200 else agent_response
    }


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    """Retrieve saved incident data."""
    incident_dir = INCIDENTS_DIR / incident_id

    if not incident_dir.exists():
        raise HTTPException(404, "Incident not found")

    return {
        "incident_id": incident_id,
        "alert": json.loads((incident_dir / "alert.json").read_text()),
        "response": (incident_dir / "response.txt").read_text() if (incident_dir / "response.txt").exists() else None,
    }


@app.get("/incidents")
def list_incidents():
    """List all incidents."""
    incidents = []
    for incident_dir in INCIDENTS_DIR.glob("*"):
        if incident_dir.is_dir():
            incidents.append({
                "id": incident_dir.name,
                "path": str(incident_dir)
            })
    return {"incidents": sorted(incidents, reverse=True)}


@app.get("/healthz")
def health():
    """Health check."""
    return {"status": "ok"}
