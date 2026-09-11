# 01 — Product Requirements Document (PRD)

## 1. Product Vision
To provide university students, visitors, faculty, staff, and emergency personnel with an intuitive, mobile-optimized, real-time spatial navigation guide that eliminates campus disorientation, resolves exact room/facility locations, and provides pedestrian directions without sacrificing privacy or relying on black-box external map providers.

---

## 2. Target Personas

### Persona A: Campus Visitor
- **Needs**: Find event halls, visitor parking, admissions office, auditoriums, and restrooms.
- **Key Pain Points**: Disoriented on large multiblock campuses, paper maps lack current location indicator, external maps only show road network without pedestrian walkways.
- **Permissions**: Public access, no authentication required.

### Persona B: Freshman / Transfer Student
- **Needs**: Quickly locate newly scheduled classrooms, computer science labs, academic departments, cafeterias, and libraries between back-to-back classes.
- **Key Pain Points**: Room numbering confusion (e.g. knowing which building and floor holds "CS-LAB-2" or "Room 204"), tight transit windows between lectures.
- **Permissions**: Public access; optional persistent profile for saved favorite rooms.

### Persona C: Faculty / Administrative Staff
- **Needs**: Direct visitors to faculty cabins, dean offices, conference halls, and administrative facilities.
- **Key Pain Points**: Repeatedly answering directional questions, inability to share exact URL links to specific campus rooms.

### Persona D: Campus Administrator / Facilities Manager
- **Needs**: Manage multi-campus boundaries, upload/update building footprints and entrance nodes, define floor plans, map out accessible ramps vs. stairs, inspect navigational audit trails, and maintain facility metadata.
- **Permissions**: Authenticated administrator with role-based access control (RBAC).

---

## 3. Core Problem Statement
Higher education and enterprise campuses are complex spatial environments featuring multi-story buildings, pedestrianized plazas, interconnected walkways, and non-intuitive room numbering schemes. Standard commercial mapping applications (Google Maps, Apple Maps) stop at the perimeter parking lot or building centroid. They fail to:
1. Distinguish specific building entrances, accessible ramps, and pedestrian pathways.
2. Resolve internal classrooms, research laboratories, and department wings.
3. Handle indoor GPS attenuation and signal jitter honestly.

---

## 4. Key Value Propositions
- **Pedestrian-First Routing**: Routes are calculated over the campus's verified pedestrian walkway graph, respecting stairs vs. accessible paths.
- **Direct Search to Exact Room**: Searches for "CS Lab", "Room 204", "Robotics", or "Library" resolve directly to the precise building entrance and floor metadata.
- **Honest Location & Privacy**: Displays actual sensor uncertainty radius, rejects jitter, provides clear indoor warnings, and stores zero personal location telemetry.
- **Multi-Tenant / Multi-Campus Scalability**: Architecture is decoupled from any hardcoded single campus, ready for multi-institution deployment.
