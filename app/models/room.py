"""
Campus Navigation System — Room Model
Represents classrooms, lecture halls, faculty offices, laboratories, and departments.
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.spatial import SpatialPoint


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    room_number = db.Column(db.String(50), nullable=False, index=True)  # e.g., "CS-101", "204"
    name = db.Column(db.String(255), nullable=False, index=True)         # e.g., "AI & Machine Learning Lab"
    floor = db.Column(db.Integer, default=0, nullable=False)            # 0 = Ground, 1 = 1st floor
    department = db.Column(db.String(150), nullable=True, index=True)   # e.g., "Computer Science"
    description = db.Column(db.Text, nullable=True)

    # Optional specific doorway coordinates
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location = db.Column(SpatialPoint, nullable=True)

    # Associated navigation node (doorway anchor)
    node_id = db.Column(db.Integer, db.ForeignKey("navigation_nodes.id", ondelete="SET NULL"), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    building = db.relationship("Building", back_populates="rooms")
    door_node = db.relationship("NavigationNode", foreign_keys=[node_id])

    __table_args__ = (
        db.UniqueConstraint("building_id", "room_number", name="uq_building_room_number"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "building_name": self.building.name if self.building else None,
            "building_code": self.building.code if self.building else None,
            "room_number": self.room_number,
            "name": self.name,
            "floor": self.floor,
            "department": self.department,
            "description": self.description,
            "coordinates": {
                "latitude": self.latitude or (self.building.latitude if self.building else None),
                "longitude": self.longitude or (self.building.longitude if self.building else None),
            },
            "node_id": self.node_id,
        }
