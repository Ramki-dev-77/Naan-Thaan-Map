"""
Campus Navigation System — Facility Model
Represents points of interest, parking zones, medical centers, cafeterias, and ATMs.
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.spatial import SpatialPoint


class Facility(db.Model):
    __tablename__ = "facilities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campus_id = db.Column(db.Integer, db.ForeignKey("campuses.id", ondelete="CASCADE"), nullable=False, index=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(SpatialPoint, nullable=True)

    accessible = db.Column(db.Boolean, default=True, nullable=False)
    opening_hours = db.Column(db.String(100), nullable=True)  # e.g., "08:00 - 20:00"

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    campus = db.relationship("Campus", back_populates="facilities")
    building = db.relationship("Building", back_populates="facilities")
    category = db.relationship("Category", back_populates="facilities")

    def to_dict(self):
        return {
            "id": self.id,
            "campus_id": self.campus_id,
            "building_id": self.building_id,
            "building_name": self.building.name if self.building else None,
            "category": self.category.to_dict() if self.category else None,
            "name": self.name,
            "description": self.description,
            "coordinates": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "accessible": self.accessible,
            "opening_hours": self.opening_hours,
        }
