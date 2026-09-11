# 11 — Backend Architecture & Service Layer Pattern

## 1. Directory Structure

```
app/
├── __init__.py           # Application Factory: create_app()
├── config.py             # Environment configurations (Development, Production, Testing)
├── extensions.py         # SQLAlchemy, Migrate, Limiter, CSRF instances
├── commands/             # Flask CLI commands (seed-demo, create-admin)
│   ├── __init__.py
│   └── seed.py
├── models/               # SQLAlchemy ORM models with GeoAlchemy2
│   ├── __init__.py
│   ├── campus.py
│   ├── building.py
│   ├── room.py
│   ├── facility.py
│   ├── category.py
│   ├── navigation.py
│   ├── admin.py
│   └── audit.py
├── api/                  # Versioned API Blueprint
│   └── v1/
│       ├── __init__.py
│       ├── campuses.py
│       ├── search.py
│       ├── locations.py
│       ├── routes.py
│       ├── facilities.py
│       └── admin.py
├── services/             # Pure Domain & Business Logic Services
│   ├── __init__.py
│   ├── routing_service.py     # A* graph pathfinder & distance engine
│   ├── search_service.py      # Trigram / fuzzy text matching & ranker
│   ├── location_service.py    # Spatial snapping & GeoJSON transformer
│   └── validation_service.py  # Coordinates & geometry boundary validator
├── utils/                # Utilities & Middleware
│   ├── errors.py              # Centralized JSON error handlers
│   ├── logging.py             # Structured JSON logger
│   └── security.py            # Password hashing, decorators, CSRF
├── templates/            # Jinja2 templates (index.html, admin/, base.html)
└── static/               # Assets (css/, js/)
```

---

## 2. The Application Factory Pattern
The application uses the standard Flask factory function `create_app(config_name=None)`:
1. Loads configuration from `app/config.py` based on `APP_ENV` environment variable.
2. Initializes extensions (`db.init_app`, `migrate.init_app`, `limiter.init_app`, `csrf.init_app`).
3. Registers Blueprints (`api_v1_bp`, `admin_bp`, `main_bp`).
4. Registers centralized error handlers for `400`, `401`, `403`, `404`, `429`, and `500`.
5. Sets up request context lifecycle hooks (generating a unique `X-Request-Id` and timing request duration for structured logging).

---

## 3. Thin Controller / Thick Service Pattern

Route handlers in `app/api/v1/` contain zero business logic. They adhere to the pattern:
```
[HTTP Request]
     │
     ▼
[Input Validation & Parsing] (Marshmallow / Schema Validator)
     │
     ▼
[Domain Service Invocation]  (e.g., RoutingService.calculate_route)
     │
     ▼
[Entity Transformation / Serialization]
     │
     ▼
[Consistent JSON Response with Meta]
```

### Example:
```python
@routes_bp.route('', methods=['POST'])
@limiter.limit("30 per minute")
def calculate_route():
    payload = request.get_json() or {}
    # Validation
    origin, destination, options = ValidationService.validate_route_request(payload)
    # Execution
    result = RoutingService.find_optimal_route(origin, destination, options)
    # Response
    return jsonify({
        "status": "success",
        "data": result,
        "meta": {"request_id": g.request_id}
    })
```
