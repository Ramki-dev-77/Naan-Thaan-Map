# 10 — Frontend Architecture & UI/UX Design

## 1. Design Philosophy
- **Mobile-First Responsive Layout**: Built to behave like a progressive web application on iOS Safari and Android Chrome, while offering a full-featured multi-pane dashboard on desktop displays.
- **Zero Heavy Build Tooling**: Pure ES6 modules, native Fetch API, and standard CSS3 variables. No complex Webpack/Vite build steps needed for production runtime, ensuring instantaneous debugging and rapid cold loads.
- **Accessible & High-Contrast**: Designed according to WCAG 2.1 AA with distinct color coding, ARIA live feedback, and touch-target sizes exceeding 48x48 px.

---

## 2. Directory Structure & Module Breakdown

```
app/static/
├── css/
│   ├── app.css           # Global reset, typography, color palette, responsive grid
│   ├── map.css           # Leaflet overrides, marker pins, accuracy halo, route polyline
│   └── responsive.css    # Breakpoints (desktop side-panel vs mobile bottom-sheet)
└── js/
    ├── app.js            # Main bootstrap, event orchestration, state store
    ├── map.js            # Leaflet map instance, tile layers, GeoJSON feature rendering
    ├── search.js         # Input debouncing, API querying, result dropdown cards
    ├── navigation.js     # Route drawer, turn-by-turn cards, recalculation watcher
    ├── geolocation.js    # WatchPosition wrapper, accuracy classification, smoothing
    ├── api.js            # Centralized fetch wrapper with standard error handling
    └── admin.js          # Admin dashboard UI, interactive node/edge/building editor
```

---

## 3. UI Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  [Top Header] Campus Title & Active Campus Selector  [Admin] │
├──────────────────────────────────────────────────────────────┤
│  [Search Bar] "Search building, room, lab, office, ATM..."   │
│  [Category Pills] All | Academic | Dining | Parking | Clinic │
├──────────────────────────────┬───────────────────────────────┤
│                              │                               │
│      [Left Side Panel]       │        [Leaflet Canvas]       │
│  (Desktop: Persistent Panel; │                               │
│   Mobile: Bottom Drawer)     │   - Campus Perimeter          │
│                              │   - Building Polygons         │
│  - Search Results List       │   - Facility Pins             │
│  - Destination Card          │   - Route Polyline            │
│  - Navigation Controls       │   - Current Location Marker   │
│    * Origin Selection        │     & Accuracy Uncertainty    │
│    * Accessible Route Toggle │     Circle                    │
│    * Distance & ETA          │                               │
│    * Step-by-Step Directions │   [Floating Map Controls]     │
│                              │   - My Location Pin           │
│                              │   - Reset View                │
│                              │   - Zoom In / Out             │
└──────────────────────────────┴───────────────────────────────┘
```

---

## 4. State Management (Vanilla Pub/Sub)
The client maintains a unified application state object:
```javascript
const AppState = {
  activeCampus: null,
  currentLocation: null,      // { lat, lng, accuracy, tier, timestamp }
  selectedDestination: null,  // { id, name, type, building, lat, lng }
  activeRoute: null,          // { distance, duration, steps, geometry }
  navigationActive: false,
  accessibleOnly: false
};
```
Modules emit custom DOM events (`state:location-update`, `state:destination-selected`, `state:route-calculated`) to decouple Leaflet rendering from search and UI panels.
