"""
Campus Navigation System — Navigation Graph Models
Models the campus pedestrian walkable network: Nodes (junctions, doors, ramps, stairs)
and Edges (pathways with distance, accessibility, and surface attributes).
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.spatial import SpatialPoint, SpatialLineString


class NavigationNode(db.Model):
    __tablename__ = "navigation_nodes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer, db.ForeignKey("campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True, index=True)

    # Node types: 'ENTRANCE', 'JUNCTION', 'STAIRS', 'RAMP', 'ELEVATOR', 'DOOR', 'CORRIDOR'
    node_type = db.Column(db.String(50), default="JUNCTION", nullable=False, index=True)
    label = db.Column(db.String(150), nullable=True)  # e.g., "CS Block North Entrance"
    floor = db.Column(db.Integer, default=0, nullable=False)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(SpatialPoint, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    campus = db.relationship("Campus", back_populates="navigation_nodes")
    building = db.relationship("Building", back_populates="navigation_nodes")

    outgoing_edges = db.relationship(
        "NavigationEdge",
        foreign_keys="NavigationEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges = db.relationship(
        "NavigationEdge",
        foreign_keys="NavigationEdge.destination_node_id",
        back_populates="destination_node",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "campus_id": self.campus_id,
            "building_id": self.building_id,
            "node_type": self.node_type,
            "label": self.label,
            "floor": self.floor,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "is_active": self.is_active,
        }


class NavigationEdge(db.Model):
    __tablename__ = "navigation_edges"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_node_id = db.Column(db.Integer, db.ForeignKey("navigation_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    destination_node_id = db.Column(db.Integer, db.ForeignKey("navigation_nodes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Physical distance in meters
    distance = db.Column(db.Float, nullable=False)
    
    # Accessibility routing flags
    accessible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    stairs = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Path types: 'PAVED_WALKWAY', 'RAMP', 'STAIRWAY', 'CORRIDOR', 'ELEVATOR', 'CROSSWALK'
    path_type = db.Column(db.String(50), default="PAVED_WALKWAY", nullable=False)
    is_bidirectional = db.Column(db.Boolean, default=True, nullable=False)

    # Geometry line for visual rendering if needed
    geometry = db.Column(SpatialLineString, nullable=True)

    # Relationships
    source_node = db.relationship("NavigationNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    destination_node = db.relationship("NavigationNode", foreign_keys=[destination_node_id], back_populates="incoming_edges")

    def to_dict(self):
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "distance": round(self.distance, 2),
            "accessible": self.accessible,
            "stairs": self.stairs,
            "path_type": self.path_type,
            "is_bidirectional": self.is_bidirectional,
        }
