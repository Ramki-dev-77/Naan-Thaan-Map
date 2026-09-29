"""
Campus Navigation System — Room Model
Represents classrooms, lecture halls, faculty offices, laboratories, and departments.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class Room(metaclass=_ModelMeta):
    id = ColumnField("Room", "id")
    building_id = ColumnField("Room", "building_id")
    room_number = ColumnField("Room", "room_number")
    name = ColumnField("Room", "name")
    department = ColumnField("Room", "department")

    def __init__(
        self,
        id: int = None,
        building_id: int = None,
        room_number: str = "",
        name: str = "",
        floor: int = 0,
        department: str = "",
        description: str = "",
        latitude: float = None,
        longitude: float = None,
        node_id: int = None,
        created_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.building_id = int(building_id) if building_id is not None else None
        self.room_number = room_number
        self.name = name
        self.floor = int(floor) if floor is not None else 0
        self.department = department
        self.description = description
        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None
        self.node_id = int(node_id) if node_id is not None else None
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

        # Relationships
        self.building = None
        self.door_node = None

    @classmethod
    def get(cls, room_id: int):
        return data_store.get_by_id(cls, room_id)

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

    def __repr__(self):
        return f"<Room id={self.id} num='{self.room_number}' name='{self.name}'>"
