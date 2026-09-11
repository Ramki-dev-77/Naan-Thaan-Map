"""
Campus Navigation System — Building Model
Represents campus blocks/structures with footprints, entrance locations, and floor counts.
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.spatial import SpatialPoint, SpatialPolygon


class Building(db.Model):
    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer, db.ForeignKey("campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    code = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'CSB', 'ADM'
    description = db.Column(db.Text, nullable=True)

    # Centroid coordinate
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(SpatialPoint, nullable=True)

    # Primary entrance coordinate (for route targeting)
    entrance_latitude = db.Column(db.Float, nullable=True)
    entrance_longitude = db.Column(db.Float, nullable=True)

    # Building polygon outline
    footprint = db.Column(SpatialPolygon, nullable=True)

    floors = db.Column(db.Integer, default=1, nullable=False)
    accessible = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    campus = db.relationship("Campus", back_populates="buildings")
    rooms = db.relationship("Room", back_populates="building", cascade="all, delete-orphan")
    facilities = db.relationship("Facility", back_populates="building")
    navigation_nodes = db.relationship("NavigationNode", back_populates="building")

    __table_args__ = (
        db.UniqueConstraint("campus_id", "code", name="uq_campus_building_code"),
    )

    def to_dict(self, include_rooms=False):
        data = {
            "id": self.id,
            "campus_id": self.campus_id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "floors": self.floors,
            "accessible": self.accessible,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "entrance": {
                "latitude": self.entrance_latitude or self.latitude,
                "longitude": self.entrance_longitude or self.longitude,
            },
            "footprint": self.footprint,
        }
        if include_rooms:
            data["rooms"] = [r.to_dict() for r in self.rooms]
        return data
