from fastapi import FastAPI
import httpx
from datetime import datetime
import asyncio
import os

app = FastAPI(title="Eye of Thundera Monitor")


MONITORED_SERVICE = {
    "name": "Eye of Thundera",
    "health_url": "http://app:8000/health",
    "check_interval_seconds": 10
}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_check = {
    "service": MONITORED_SERVICE["name"],
    "url": MONITORED_SERVICE["health_url"],
    "status": "unknown",
    "severity": "info",
    "http_status": None,
    "checked_at": None,
    "details": "No checks performed yet"
}

current_incident = None
incident_history = []


def now_iso():
    return datetime.utcnow().isoformat()


def get_severity_from_status(status: str) -> str:
    if status == "down":
        return "critical"
    if status == "unhealthy":
        return "warning"
    if status == "healthy":
        return "resolved"
    return "info"


def get_incident_title(severity: str) -> str:
    if severity == "critical":
        return "🔴 CRITICAL INCIDENT"
    if severity == "warning":
        return "🟡 WARNING INCIDENT"
    if severity == "resolved":
        return "✅ INCIDENT RESOLVED"
    return "ℹ️ INCIDENT UPDATE"


async def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram is not configured. Skipping alert.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

        if response.status_code != 200:
            print(f"Failed to send Telegram message: {response.text}")

    except Exception as e:
        print(f"Error sending Telegram message: {e}")


async def perform_health_check():
    global last_check

    previous_status = last_check["status"]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(MONITORED_SERVICE["health_url"])

        if response.status_code == 200:
            new_status = "healthy"
            http_status = response.status_code
            details = "Service responded successfully"
        else:
            new_status = "unhealthy"
            http_status = response.status_code
            details = f"Service responded with unexpected status {response.status_code}"

    except Exception as e:
        new_status = "down"
        http_status = None
        details = f"Failed to connect: {str(e)}"

    severity = get_severity_from_status(new_status)

    last_check = {
        "service": MONITORED_SERVICE["name"],
        "url": MONITORED_SERVICE["health_url"],
        "status": new_status,
        "severity": severity,
        "http_status": http_status,
        "checked_at": now_iso(),
        "details": details
    }

    await handle_incident_transition(previous_status, new_status, details, severity)


async def handle_incident_transition(previous_status, new_status, details, severity):
    global current_incident, incident_history

    bad_states = {"unhealthy", "down"}

    # abre incidente
    if previous_status not in bad_states and new_status in bad_states:
        current_incident = {
            "id": len(incident_history) + 1,
            "service": MONITORED_SERVICE["name"],
            "status": "open",
            "severity": severity,
            "started_at": now_iso(),
            "resolved_at": None,
            "initial_state": new_status,
            "current_state": new_status,
            "details": details
        }
        incident_history.append(current_incident.copy())

        message = (
            f"{get_incident_title(severity)}\n"
            f"Service: {MONITORED_SERVICE['name']}\n"
            f"Severity: {severity}\n"
            f"State: {new_status}\n"
            f"Details: {details}\n"
            f"Started at: {current_incident['started_at']}"
        )
        await send_telegram_message(message)

    # atualiza incidente aberto
    elif current_incident and current_incident["status"] == "open" and new_status in bad_states:
        current_incident["current_state"] = new_status
        current_incident["severity"] = severity
        current_incident["details"] = details
        incident_history[-1] = current_incident.copy()

    # resolve incidente
    elif current_incident and current_incident["status"] == "open" and new_status == "healthy":
        resolved_at = now_iso()

        current_incident["status"] = "resolved"
        current_incident["resolved_at"] = resolved_at
        current_incident["current_state"] = new_status
        current_incident["details"] = "Service recovered"

        incident_history[-1] = current_incident.copy()

        message = (
            f"{get_incident_title('resolved')}\n"
            f"Service: {MONITORED_SERVICE['name']}\n"
            f"Previous severity: {current_incident['severity']}\n"
            f"Recovered at: {resolved_at}\n"
            f"Details: Service recovered"
        )
        await send_telegram_message(message)

        current_incident = None


async def monitoring_loop():
    while True:
        await perform_health_check()
        await asyncio.sleep(MONITORED_SERVICE["check_interval_seconds"])


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitoring_loop())


@app.get("/")
def root():
    return {
        "message": "Ops API is running",
        "monitored_service": MONITORED_SERVICE,
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    }


@app.get("/check")
async def check_service():
    await perform_health_check()
    return last_check


@app.get("/status")
def get_status():
    return last_check


@app.get("/incident")
def get_current_incident():
    if current_incident:
        return current_incident

    return {"message": "No active incident"}


@app.get("/incidents")
def get_incident_history():
    return {
        "total": len(incident_history),
        "items": incident_history
    }