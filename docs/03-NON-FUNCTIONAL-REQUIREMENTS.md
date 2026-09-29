# 03 — Non-Functional Requirements (NFR)

## 1. Performance & Latency Targets
- **NFR-PERF-001**: **Initial Map & Bundle Load**: Total initial frontend payload < 350 KB compressed; DOM ready and map initialized in < 1.5 seconds on a 4G connection.
- **NFR-PERF-002**: **Search Latency**: Search API response time `P95 < 80 ms` for the bundled campus dataset.
- **NFR-PERF-003**: **Routing Calculation Latency**: A* graph pathfinding `P95 < 40 ms` for graph networks up to 2,000 nodes.
- **NFR-PERF-004**: **Concurrency**: Single Cloud Run instance (2 vCPU, 2 GB RAM) handles at least 250 requests per second; auto-scales up to 1,000+ concurrent active sessions without degradation.

---

## 2. Scalability & Architecture
- **NFR-SCAL-001**: **Multi-Campus Data Isolation**: Entity records carry `campus_id` references and API queries filter by campus.
- **NFR-SCAL-002**: **Stateless Application Layer**: No database or persistent local storage; bundled JSON is loaded at startup. Admin mutations are transient and must not be treated as durable.
- **NFR-SCAL-003**: **No Database Connections**: The service performs no database connection or pool management.

---

## 3. Reliability & Availability
- **NFR-REL-001**: **Target SLA**: 99.9% uptime in production on Google Cloud Run.
- **NFR-REL-002**: **Graceful Degradation**: If browser geolocation is denied or times out, the system operates completely on manual origin selection without runtime errors.
- **NFR-REL-003**: **Static Data Integrity**: Validate JSON datasets before deployment and verify readiness after startup; restore data changes by redeploying a known-good revision.

---

## 4. Security & Privacy
- **NFR-SEC-001**: **Zero Geolocation Persistence**: Client GPS coordinates are processed exclusively in client-side memory or transiently inside routing requests; coordinates are never saved to disk or logged.
- **NFR-SEC-002**: **Transport Security**: Enforced HTTPS/TLS 1.3 across all endpoints. HSTS header enabled in production.
- **NFR-SEC-003**: **Authentication**: Passwords hashed using industry-standard modern adaptive hashing (Werkzeug `scrypt` or `pbkdf2:sha256`).
- **NFR-SEC-004**: **Session & Cookie Hardening**: `HttpOnly=True`, `Secure=True` (in prod), `SameSite=Lax`.
- **NFR-SEC-005**: **CSRF & Rate Limiting**: Token-based CSRF protection on forms and state-changing APIs; Flask-Limiter enforcing 60 requests/minute on search and 30 requests/minute on route calculations.

---

## 5. Accessibility (WCAG 2.1 AA)
- **NFR-ACC-001**: All interactive elements (search bar, filter buttons, route modal) are keyboard accessible with visible focus rings.
- **NFR-ACC-002**: ARIA live regions announce location status, route updates, and error alerts to screen readers.
- **NFR-ACC-003**: High color contrast (≥ 4.5:1 ratio) on map markers, route polylines, and UI typography.
- **NFR-ACC-004**: Non-visual textual representations for all spatial directions and facilities.
