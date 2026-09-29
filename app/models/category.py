"""
Campus Navigation System — Category Model
Provides taxonomical grouping with icons and UI badges.
Zero-database in-memory model backed by data_store.
"""
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class Category(metaclass=_ModelMeta):
    id = ColumnField("Category", "id")
    name = ColumnField("Category", "name")
    slug = ColumnField("Category", "slug")

    def __init__(
        self,
        id: int = None,
        name: str = "",
        slug: str = "",
        icon: str = "map-pin",
        color: str = "#2563eb",
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.name = name
        self.slug = slug
        self.icon = icon
        self.color = color
        self.facilities = []

    @classmethod
    def get(cls, cat_id: int):
        return data_store.get_by_id(cls, cat_id)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "icon": self.icon,
            "color": self.color,
        }

    def __repr__(self):
        return f"<Category id={self.id} name='{self.name}'>"
