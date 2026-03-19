from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = FastAPI(title="Eye Of Thundera Project")


# =========================
# Estado interno da aplicação
# =========================
app_state = {
    "healthy": True,
    "slow_mode": False,
    "error_mode": False
}


# =========================
# Métricas Prometheus
# =========================
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"]
)

ERROR_COUNT = Counter(
    "http_errors_total",
    "Total number of HTTP error responses",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)


# =========================
# Middleware para métricas
# =========================
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception:
        status_code = "500"
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        raise

    duration = time.time() - start_time

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint, http_status=status_code).inc()

    return response


# =========================
# Função auxiliar
# =========================
def apply_modes():
    """
    Aplica os modos globais da aplicação.
    slow_mode: adiciona atraso artificial
    error_mode: força erro 500
    """
    if app_state["slow_mode"]:
        time.sleep(5)

    if app_state["error_mode"]:
        raise HTTPException(status_code=500, detail="Global error mode enabled")


# =========================
# Endpoints básicos
# =========================
@app.get("/")
def root():
    apply_modes()
    return {"message": "Eye Of Thundera is running"}


@app.get("/health")
def health():
    """
    Healthcheck principal.
    Se healthy=False, retorna 503.
    """
    if not app_state["healthy"]:
        raise HTTPException(status_code=503, detail="Application is unhealthy")

    return {"status": "ok"}


@app.get("/ready")
def ready():
    """
    Readiness check.
    Pode ser usado para simular se a app está pronta para receber tráfego.
    """
    if not app_state["healthy"]:
        raise HTTPException(status_code=503, detail="Application is not ready")

    return {"status": "ready"}


@app.get("/status")
def status():
    """
    Mostra o estado atual da aplicação.
    """
    return {
        "healthy": app_state["healthy"],
        "slow_mode": app_state["slow_mode"],
        "error_mode": app_state["error_mode"]
    }


# =========================
# Endpoints de simulação
# =========================
@app.get("/slow")
def slow():
    time.sleep(5)
    return {"status": "slow response", "delay_seconds": 5}


@app.get("/fail")
def fail():
    raise HTTPException(status_code=500, detail="Simulated failure")


@app.get("/random-fail")
def random_fail():
    """
    Falha aleatoriamente em cerca de 30% das requisições.
    """
    apply_modes()

    if random.random() < 0.3:
        raise HTTPException(status_code=500, detail="Random simulated failure")

    return {"status": "success", "message": "Request passed this time"}


@app.get("/load")
def load():
    """
    Simula carga de CPU por alguns segundos.
    """
    apply_modes()

    start = time.time()
    while time.time() - start < 3:
        sum(i * i for i in range(10000))

    return {"status": "load completed", "duration_seconds": 3}


# =========================
# Endpoints de controle
# =========================
@app.post("/toggle-health")
def toggle_health():
    app_state["healthy"] = not app_state["healthy"]
    return {
        "message": "Health status toggled",
        "healthy": app_state["healthy"]
    }


@app.post("/toggle-slow")
def toggle_slow():
    app_state["slow_mode"] = not app_state["slow_mode"]
    return {
        "message": "Slow mode toggled",
        "slow_mode": app_state["slow_mode"]
    }


@app.post("/toggle-error")
def toggle_error():
    app_state["error_mode"] = not app_state["error_mode"]
    return {
        "message": "Error mode toggled",
        "error_mode": app_state["error_mode"]
    }


@app.post("/reset")
def reset():
    app_state["healthy"] = True
    app_state["slow_mode"] = False
    app_state["error_mode"] = False

    return {
        "message": "Application state reset",
        "state": app_state
    }


# =========================
# Métricas
# =========================
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)