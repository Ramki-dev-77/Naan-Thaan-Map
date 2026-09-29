# 00 — Master Prompt & Architectural Directives

## Executive Overview
This document records the master requirements, architectural rules, operational constraints, and quality requirements for the **Campus Navigation System**.

The platform is a multi-campus interactive navigation system supporting campus pedestrian routing, location accuracy UX, role-based administration, and stateless deployment to Google Cloud Run. Campus data is bundled as static JSON; no database service is required.

---

## Core Tenets & Architectural Non-Negotiables

1. **Provider Independence**:
   - Campus map data (buildings, footprints, rooms, entrances, pedestrian paths, facilities) is maintained in version-controlled JSON files under `app/data/`.
   - The platform never assumes commercial third-party maps (e.g. Google Maps or OpenStreetMap) possess internal building layouts or room-level topology.
   - Routing uses a high-performance in-memory graph search (A* algorithm) computed over verified campus pedestrian edges.
   - External routing providers (e.g., Google Routes API) are abstracted behind an interchangeable service interface and invoked only when requested outside the campus boundary.

2. **Honest Geolocation & Accuracy UX**:
   - Geolocation relies on the standard W3C Browser Geolocation API (`navigator.geolocation.watchPosition`).
   - Browser geolocation is explicitly requested only when navigation or "My Location" is activated—never silently.
   - False precision is strictly prohibited: GPS uncertainty is displayed numerically (`±X m`) and categorized into clear UX states:
     - `≤ 10 m`: **Excellent**
     - `10 – 25 m`: **Good**
     - `25 – 50 m`: **Usable**
     - `50 – 100 m`: **Approximate**
     - `> 100 m`: **Poor**
   - Jitter filtering rejects impossible sudden position jumps.
   - Users are explicitly informed that GPS signal degrades significantly inside buildings; manual origin selection is provided as a seamless fallback.

3. **Multi-Campus Static Spatial Data Model**:
   - Spatial geometries use GeoJSON-compatible WGS84 longitude/latitude coordinates.
   - Core domain models: `Campus`, `Building`, `Room`, `Facility`, `Category`, `NavigationNode`, `NavigationEdge`, `AdminUser`, `AuditLog`.

4. **Security & Privacy by Design**:
   - Zero persistent storage of raw user geolocation coordinates.
   - HTTPS enforced in production with secure cookies (`HttpOnly`, `SameSite=Lax`, `Secure`).
   - CSRF protection on state-mutating requests and Flask-Limiter rate limiting on search/routing endpoints.
   - Admin authentication enforced server-side with secure password hashing (Argon2 / Scrypt / PBKDF2).

5. **Cloud-Native Google Cloud Architecture**:
   - Deployable as a stateless container to **Google Cloud Run**.
   - Campus JSON files are bundled with the application image; persistent data changes are made in source and deployed as a new revision.
   - Production secrets managed via **Google Secret Manager**.
   - Structured JSON logging compatible with **Google Cloud Logging**.
   - Readiness (`/ready`) and Liveness (`/health`) health probes.
