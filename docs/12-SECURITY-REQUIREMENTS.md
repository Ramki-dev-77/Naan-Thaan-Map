# 12 — Security & Compliance Architecture

## 1. Threat Modeling & Defense in Depth

| Threat Vector | Potential Impact | Architecture Mitigation |
|---|---|---|
| **Invalid Coordinate / Geometry Input** | Malformed route or map data | Request coordinates are parsed and range-checked; static geometry is maintained in reviewed JSON files. |
| **Cross-Site Scripting (XSS)** | Token theft, malicious map redirects | Jinja2 auto-escaping enabled; Content Security Policy (CSP) headers restricting script sources to trusted origins. |
| **Cross-Site Request Forgery (CSRF)** | Unauthorized administrative state changes | Flask-WTF CSRF tokens required on all POST, PUT, DELETE operations. |
| **Denial of Service / Scraping** | Backend overload, map scraping | Flask-Limiter enforcing IP-based rate limits (60/min search, 30/min routing). Cloud Armor at ingress. |
| **Credential Compromise** | Unauthorized campus topology tampering | Passwords hashed using modern adaptive hashing (scrypt / Argon2). Brute-force lockout and rate limits on `/admin/login`. |
| **Location Data Leakage** | User stalking / tracking liability | **Zero persistence policy**: User GPS coordinates are processed exclusively in client-side memory; coordinates are strictly forbidden in access logs. |

---

## 2. HTTP Security Headers
All responses emit hardened security headers configured via middleware:
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; font-src 'self'; connect-src 'self';
```

---

## 3. Session & Cookie Security Configuration
In production environments:
```python
SESSION_COOKIE_SECURE = True       # Transmitted only over HTTPS
SESSION_COOKIE_HTTPONLY = True     # Inaccessible to document.cookie (XSS protection)
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF mitigation
PERMANENT_SESSION_LIFETIME = 1800  # 30-minute auto-expiry for admin sessions
```

---

## 4. Immutable Administrative Audit Logging
Every modifying administrative action (`CREATE`, `UPDATE`, `DELETE`) generates an immutable `AuditLog` row capturing:
- `admin_id`: Authenticated user ID.
- `action`: E.g. `CREATE_BUILDING`, `UPDATE_NODE`, `DELETE_ROOM`.
- `entity_type` & `entity_id`: Target object reference.
- `metadata`: JSON snapshot of changed attributes before/after mutation.
- `ip_address`: Client IP address.
- `created_at`: UTC timestamp.
