"""
Campus Navigation System — Campus Model
Supports multi-campus isolation and campus boundary polygons.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class Campus(metaclass=_ModelMeta):
    id = ColumnField("Campus", "id")
    name = ColumnField("Campus", "name")
    slug = ColumnField("Campus", "slug")
    is_active = ColumnField("Campus", "is_active")

    def __init__(
        self,
        id: int = None,
        name: str = "",
        slug: str = "",
        description: str = "",
        latitude: float = 0.0,
        longitude: float = 0.0,
        boundary: dict = None,
        is_active: bool = True,
        created_at: str = None,
        updated_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.name = name
        self.slug = slug
        self.description = description
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.boundary = boundary
        self.is_active = bool(is_active)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()

        # Relationships (populated by data_store)
        self.buildings = []
        self.facilities = []
        self.navigation_nodes = []

    @classmethod
    def get(cls, campus_id: int):
        return data_store.get_by_id(cls, campus_id)

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
            "created_at": self.created_at if isinstance(self.created_at, str) else self.created_at.isoformat(),
        }
        if include_boundary and self.boundary:
            data["boundary"] = self.boundary
        return data

    def __repr__(self):
        return f"<Campus id={self.id} name='{self.name}'>"
