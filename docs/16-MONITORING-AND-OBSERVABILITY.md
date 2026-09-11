# 16 — Monitoring, Observability & Health Probes

## 1. Structured JSON Logging Architecture
In compliance with Google Cloud Logging specifications, all stdout/stderr emissions from Flask and Gunicorn are formatted as single-line JSON objects with standardized severity fields:

```json
{
  "timestamp": "2026-09-11T17:15:32.412Z",
  "severity": "INFO",
  "message": "Calculated pedestrian route",
  "httpRequest": {
    "requestMethod": "POST",
    "requestUrl": "/api/v1/routes",
    "status": 200,
    "latency": "0.038s",
    "userAgent": "Mozilla/5.0 (iPhone; CPU OS 17_0 like Mac OS X)",
    "remoteIp": "203.0.113.42"
  },
  "logging.googleapis.com/trace": "projects/PROJECT_ID/traces/TRACE_ID",
  "requestId": "req-98f21cae",
  "campusId": 1,
  "routeDistance": 245.5,
  "algorithm": "A_STAR"
}
```

### Sanitization Rule:
Under no circumstances are user exact coordinates, authorization passwords, session cookies, or secret API keys written to structured logs.

---

## 2. Health Probes Specification
- **Process Liveness Probe (`GET /health`)**:
  - Purpose: Validates that Gunicorn worker is accepting HTTP requests and has not deadlocked.
  - Return: HTTP 200 `{"status": "ok", "uptime_seconds": 18240}`.
  - Dependency: Zero database ping to avoid cascading failovers under DB load.
- **Dependency Readiness Probe (`GET /ready`)**:
  - Purpose: Validates database connection pool and spatial extension readiness before routing traffic to a newly started container.
  - Return: HTTP 200 `{"status": "ready", "database": "connected", "postgis": "available"}`.

---

## 3. Production Alerting Policies (Google Cloud Monitoring)

1. **High 5xx Error Rate**:
   - Condition: `sum(rate(cloudrun.googleapis.com/request_count{response_code_class="5xx"}))` > 2% for 5 minutes.
   - Severity: Critical (PagerDuty / SMS notification).
2. **High P95 Latency Spike**:
   - Condition: Route calculation response time `P95 > 500 ms` for 10 minutes.
   - Severity: Warning (Slack alert).
3. **Database Connection Saturation**:
   - Condition: Active connections / Max connections > 85%.
   - Action: Check connection leak or increase Cloud SQL tier.
