"""
Campus Navigation System — Facility Model
Represents points of interest, parking zones, medical centers, cafeterias, and ATMs.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class Facility(metaclass=_ModelMeta):
    id = ColumnField("Facility", "id")
    campus_id = ColumnField("Facility", "campus_id")
    building_id = ColumnField("Facility", "building_id")
    category_id = ColumnField("Facility", "category_id")
    name = ColumnField("Facility", "name")

    def __init__(
        self,
        id: int = None,
        campus_id: int = None,
        building_id: int = None,
        category_id: int = None,
        name: str = "",
        description: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        accessible: bool = True,
        opening_hours: str = None,
        created_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.campus_id = int(campus_id) if campus_id is not None else None
        self.building_id = int(building_id) if building_id is not None else None
        self.category_id = int(category_id) if category_id is not None else None
        self.name = name
        self.description = description
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.accessible = bool(accessible)
        self.opening_hours = opening_hours
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

        # Relationships
        self.campus = None
        self.building = None
        self.category = None

    @classmethod
    def get(cls, fac_id: int):
        return data_store.get_by_id(cls, fac_id)

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

    def __repr__(self):
        return f"<Facility id={self.id} name='{self.name}'>"
