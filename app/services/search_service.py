"""
Campus Navigation System — Search Service
Implements tiered ranking across buildings, rooms, departments, and facilities.
Ranks: 1. Exact match, 2. Prefix match, 3. Strong substring match, 4. Fuzzy match.
Zero-database implementation reading from in-memory data store.
"""
import re
from difflib import SequenceMatcher
from app.models.building import Building
from app.models.room import Room
from app.models.facility import Facility
from app.models.category import Category


class SearchService:
    @staticmethod
    def _fuzzy_score(query_lower: str, target_text: str) -> float:
        """Calculate similarity ratio between 0.0 and 1.0."""
        if not target_text:
            return 0.0
        target_lower = target_text.lower()
        if query_lower == target_lower:
            return 1.0
        if target_lower.startswith(query_lower):
            return 0.95
        if query_lower in target_lower:
            return 0.85
        return SequenceMatcher(None, query_lower, target_lower).ratio()

    @classmethod
    def search(cls, query: str, campus_id: int = None, category_slug: str = None, limit: int = 15):
        """Execute multi-entity search and return ranked results."""
        clean_query = query.strip()
        is_wildcard = (not clean_query or clean_query == "*")
        if not clean_query and not category_slug:
            return []

        q_lower = clean_query.lower()
        results = []

        # 1. Search Buildings (Only if category is empty or 'academic' or 'all')
        if not category_slug or category_slug.lower() in ["academic", "all"]:
            buildings = Building.query.all()
            if campus_id:
                buildings = [b for b in buildings if b.campus_id == campus_id]

            for b in buildings:
                score = 0.0
                matched_field = "name"
                if is_wildcard:
                    score = 1.0
                elif b.code and q_lower == b.code.lower():
                    score = 1.0
                    matched_field = "code"
                elif b.code and b.code.lower().startswith(q_lower):
                    score = 0.95
                    matched_field = "code"
                else:
                    name_score = cls._fuzzy_score(q_lower, b.name)
                    desc_score = cls._fuzzy_score(q_lower, b.description or "") * 0.7
                    if name_score >= desc_score:
                        score = name_score
                        matched_field = "name"
                    else:
                        score = desc_score
                        matched_field = "description"

                if score > 0.45:
                    results.append({
                        "id": b.id,
                        "type": "building",
                        "name": b.name,
                        "code": b.code,
                        "building": b.name,
                        "floor": None,
                        "category": "Academic / Building",
                        "category_icon": "building",
                        "category_color": "#2563eb",
                        "coordinates": {
                            "latitude": b.entrance_latitude or b.latitude,
                            "longitude": b.entrance_longitude or b.longitude,
                        },
                        "description": b.description or f"Building Code: {b.code}",
                        "relevance": round(score, 3),
                    })

        # 2. Search Rooms (Only if category is empty or 'academic' or 'all')
        if not category_slug or category_slug.lower() in ["academic", "all"]:
            rooms = Room.query.all()
            if campus_id:
                rooms = [r for r in rooms if r.building and r.building.campus_id == campus_id]

            for r in rooms:
                score = 0.0
                if is_wildcard:
                    score = 0.88
                elif r.room_number and q_lower == r.room_number.lower():
                    score = 1.0
                elif r.room_number and r.room_number.lower().startswith(q_lower):
                    score = 0.95
                elif r.room_number and q_lower in r.room_number.lower():
                    score = 0.90
                else:
                    name_score = cls._fuzzy_score(q_lower, r.name)
                    dept_score = cls._fuzzy_score(q_lower, r.department or "") * 0.8
                    desc_score = cls._fuzzy_score(q_lower, r.description or "") * 0.6
                    score = max(name_score, dept_score, desc_score)

                if score > 0.45:
                    results.append({
                        "id": r.id,
                        "type": "room",
                        "name": f"{r.room_number} — {r.name}",
                        "room_number": r.room_number,
                        "building": r.building.name if r.building else "Campus Building",
                        "building_code": r.building.code if r.building else "",
                        "floor": r.floor,
                        "department": r.department,
                        "category": "Classroom / Lab",
                        "category_icon": "door-open",
                        "category_color": "#0d9488",
                        "coordinates": {
                            "latitude": r.latitude or (r.building.entrance_latitude or r.building.latitude if r.building else None),
                            "longitude": r.longitude or (r.building.entrance_longitude or r.building.longitude if r.building else None),
                        },
                        "node_id": r.node_id,
                        "description": f"Floor {r.floor} • {r.building.name if r.building else ''}",
                        "relevance": round(score, 3),
                    })

        # 3. Search Facilities
        facilities = Facility.query.all()
        if campus_id:
            facilities = [f for f in facilities if f.campus_id == campus_id]
        if category_slug and category_slug.lower() != "all":
            facilities = [f for f in facilities if f.category and f.category.slug == category_slug]

        for f in facilities:
            if is_wildcard:
                final_score = 1.0
            else:
                score = cls._fuzzy_score(q_lower, f.name)
                cat_score = cls._fuzzy_score(q_lower, f.category.name if f.category else "") * 0.85
                desc_score = cls._fuzzy_score(q_lower, f.description or "") * 0.6
                final_score = max(score, cat_score, desc_score)

            if final_score > 0.45:
                results.append({
                    "id": f.id,
                    "type": "facility",
                    "name": f.name,
                    "building": f.building.name if f.building else "Outdoor Landmark",
                    "floor": None,
                    "category": f.category.name if f.category else "Facility",
                    "category_icon": f.category.icon if f.category else "map-pin",
                    "category_color": f.category.color if f.category else "#f59e0b",
                    "coordinates": {
                        "latitude": f.latitude,
                        "longitude": f.longitude,
                    },
                    "description": f.description or (f.category.name if f.category else "Facility"),
                    "relevance": round(final_score, 3),
                })

        # Sort descending by relevance score, then alphabetically
        results.sort(key=lambda x: (x["relevance"], x["name"]), reverse=True)
        return results[:limit]
