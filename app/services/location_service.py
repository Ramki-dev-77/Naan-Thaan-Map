"""
Campus Navigation System — Location Service
Generates unified GeoJSON feature collections for client-side map rendering
and manages campus spatial lookups.
"""
from typing import Dict, Any
from app.extensions import db
from app.models.campus import Campus
from app.models.building import Building
from app.models.facility import Facility
from app.models.navigation import NavigationNode, NavigationEdge
from app.utils.errors import AppError


class LocationService:
    @staticmethod
    def get_campus_geojson(campus_id: int) -> Dict[str, Any]:
        """
        Builds a comprehensive GeoJSON FeatureCollection containing:
        - Campus boundary polygon
        - Building footprint polygons
        - Facility point markers
        - Building entrance nodes
        - Walkway paths
        """
        campus = db.session.get(Campus, campus_id)
        if not campus:
            raise AppError("Campus not found.", code="CAMPUS_NOT_FOUND", status_code=404)

        features = []

        # 1. Campus Boundary
        if campus.boundary:
            features.append({
                "type": "Feature",
                "geometry": campus.boundary if isinstance(campus.boundary, dict) else {
                    "type": "Polygon",
                    "coordinates": campus.boundary
                },
                "properties": {
                    "layer": "campus_boundary",
                    "id": campus.id,
                    "name": campus.name,
                    "slug": campus.slug,
                }
            })

        # 2. Building Footprints
        buildings = Building.query.filter_by(campus_id=campus_id).all()
        for b in buildings:
            if b.footprint:
                geom = b.footprint if isinstance(b.footprint, dict) else {
                    "type": "Polygon",
                    "coordinates": b.footprint
                }
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "layer": "building_footprint",
                        "id": b.id,
                        "name": b.name,
                        "code": b.code,
                        "floors": b.floors,
                        "accessible": b.accessible,
                        "description": b.description,
                        "entrance": {
                            "latitude": b.entrance_latitude or b.latitude,
                            "longitude": b.entrance_longitude or b.longitude,
                        }
                    }
                })

        # 3. Facilities
        facilities = Facility.query.filter_by(campus_id=campus_id).all()
        for f in facilities:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [f.longitude, f.latitude],
                },
                "properties": {
                    "layer": "facility",
                    "id": f.id,
                    "name": f.name,
                    "category": f.category.name if f.category else "Facility",
                    "category_slug": f.category.slug if f.category else "facility",
                    "icon": f.category.icon if f.category else "map-pin",
                    "color": f.category.color if f.category else "#f59e0b",
                    "description": f.description,
                    "opening_hours": f.opening_hours,
                    "accessible": f.accessible,
                }
            })

        # 4. Building Entrances
        entrance_nodes = NavigationNode.query.filter_by(campus_id=campus_id, node_type="ENTRANCE", is_active=True).all()
        for node in entrance_nodes:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [node.longitude, node.latitude],
                },
                "properties": {
                    "layer": "entrance",
                    "id": node.id,
                    "building_id": node.building_id,
                    "label": node.label or "Entrance",
                    "floor": node.floor,
                }
            })

        # 5. Walkway Paths (Navigation Edges)
        edges = NavigationEdge.query.join(NavigationNode, NavigationEdge.source_node_id == NavigationNode.id)\
            .filter(NavigationNode.campus_id == campus_id).all()
        
        seen_edges = set()
        for e in edges:
            edge_key = tuple(sorted([e.source_node_id, e.destination_node_id]))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            src = e.source_node
            dst = e.destination_node
            if src and dst:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [src.longitude, src.latitude],
                            [dst.longitude, dst.latitude]
                        ]
                    },
                    "properties": {
                        "layer": "walkway",
                        "id": e.id,
                        "distance": round(e.distance, 1),
                        "accessible": e.accessible,
                        "stairs": e.stairs,
                        "path_type": e.path_type,
                    }
                })

        return {
            "type": "FeatureCollection",
            "campus": campus.to_dict(),
            "features": features,
        }
