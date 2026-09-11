# 19 — Future Roadmap & Architectural Extensions

While the core MVP establishes high-performance outdoor pedestrian routing, multi-attribute search, and verified campus topology, the architecture is specifically designed to support the following phased enterprise capabilities:

---

## 1. Indoor Positioning Technologies
Because browser GPS attenuates inside buildings, future phases will introduce verified indoor positioning:
- **Bluetooth Low Energy (BLE) Beacons**: Deploying low-power iBeacons along corridors for trilateration in native apps.
- **Wi-Fi 6 Fine Timing Measurement (RTT / 802.11mc)**: Sub-meter indoor distance ranging off campus enterprise access points.
- **Physical QR Code Checkpoints**: Printed QR codes at room doorways and building lobby kiosks ("You Are Here" instant origin anchor).
- **Ultra-Wideband (UWB)**: High-precision positioning for campus emergency response teams.

---

## 2. Progressive Web App (PWA) & Offline Vector Tiles
- Service Worker integration for full offline caching of application shell.
- Vector tile compression (MapLibre GL JS / Protomaps) allowing visitors to navigate without active cellular data.

---

## 3. Real-Time Campus Intelligence
- **Crowd & Congestion Avoidance**: Integrating anonymized Wi-Fi client counts per building to route pedestrians around high-traffic corridors.
- **Campus Event Routing**: Dynamic path closures for graduation ceremonies, construction work, or athletic events.
- **Shuttle Bus Tracking**: Live GTFS-RT feed of campus transit shuttles integrated into multimodal route options.

---

## 4. Enterprise Identity & SSO Integration
- Integration with university Identity Providers via **OAuth 2.0 / OpenID Connect (OIDC)** (e.g. Google Workspace, Microsoft Entra ID, Shibboleth).
- Student schedule synchronization: Automatically showing navigation to the student's next scheduled class.

---

## 5. Natural Language & Voice Assistance
- Natural language query parser mapping conversational prompts ("Where can I print my thesis near the library?") to structured database queries and nearest facility routing without inventing non-existent locations.
