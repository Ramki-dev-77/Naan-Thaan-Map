"""
Campus Navigation System — Building Model
Represents campus blocks/structures with footprints, entrance locations, and floor counts.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class Building(metaclass=_ModelMeta):
    id = ColumnField("Building", "id")
    campus_id = ColumnField("Building", "campus_id")
    name = ColumnField("Building", "name")
    code = ColumnField("Building", "code")

    def __init__(
        self,
        id: int = None,
        campus_id: int = 1,
        name: str = "",
        code: str = "",
        description: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        entrance_latitude: float = None,
        entrance_longitude: float = None,
        footprint: dict = None,
        floors: int = 1,
        accessible: bool = True,
        created_at: str = None,
        updated_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.campus_id = int(campus_id) if campus_id is not None else None
        self.name = name
        self.code = code
        self.description = description
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.entrance_latitude = float(entrance_latitude) if entrance_latitude is not None else self.latitude
        self.entrance_longitude = float(entrance_longitude) if entrance_longitude is not None else self.longitude
        self.footprint = footprint
        self.floors = int(floors) if floors is not None else 1
        self.accessible = bool(accessible)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()

        # Relationships
        self.campus = None
        self.rooms = []
        self.facilities = []
        self.navigation_nodes = []

    @classmethod
    def get(cls, building_id: int):
        return data_store.get_by_id(cls, building_id)

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

    def __repr__(self):
        return f"<Building id={self.id} code='{self.code}' name='{self.name}'>"
