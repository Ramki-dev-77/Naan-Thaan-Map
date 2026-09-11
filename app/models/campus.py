"""
Campus Navigation System — Campus Model
Supports multi-campus tenant isolation and campus boundary polygons.
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.spatial import SpatialPoint, SpatialPolygon


class Campus(db.Model):
    __tablename__ = "campuses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Geographic center coordinate (lat/lng)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(SpatialPoint, nullable=True)

    # Perimeter boundary polygon
    boundary = db.Column(SpatialPolygon, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    buildings = db.relationship("Building", back_populates="campus", cascade="all, delete-orphan")
    facilities = db.relationship("Facility", back_populates="campus", cascade="all, delete-orphan")
    navigation_nodes = db.relationship("NavigationNode", back_populates="campus", cascade="all, delete-orphan")

    def to_dict(self, include_boundary=False):
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_boundary and self.boundary:
            data["boundary"] = self.boundary
        return data
