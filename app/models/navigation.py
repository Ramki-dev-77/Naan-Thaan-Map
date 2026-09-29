"""
Campus Navigation System — Navigation Graph Models
Models the campus pedestrian walkable network: Nodes and Edges.
Zero-database in-memory models backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class NavigationNode(metaclass=_ModelMeta):
    id = ColumnField("NavigationNode", "id")
    campus_id = ColumnField("NavigationNode", "campus_id")
    building_id = ColumnField("NavigationNode", "building_id")
    node_type = ColumnField("NavigationNode", "node_type")
    label = ColumnField("NavigationNode", "label")
    is_active = ColumnField("NavigationNode", "is_active")

    def __init__(
        self,
        id: int = None,
        campus_id: int = None,
        building_id: int = None,
        node_type: str = "JUNCTION",
        label: str = None,
        floor: int = 0,
        latitude: float = 0.0,
        longitude: float = 0.0,
        is_active: bool = True,
        created_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.campus_id = int(campus_id) if campus_id is not None else None
        self.building_id = int(building_id) if building_id is not None else None
        self.node_type = node_type or "JUNCTION"
        self.label = label
        self.floor = int(floor) if floor is not None else 0
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.is_active = bool(is_active)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

        # Relationships
        self.campus = None
        self.building = None
        self.outgoing_edges = []
        self.incoming_edges = []

    @classmethod
    def get(cls, node_id: int):
        return data_store.get_by_id(cls, node_id)

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

    def __repr__(self):
        return f"<NavigationNode id={self.id} type='{self.node_type}' label='{self.label}'>"


class NavigationEdge(metaclass=_ModelMeta):
    id = ColumnField("NavigationEdge", "id")
    source_node_id = ColumnField("NavigationEdge", "source_node_id")
    destination_node_id = ColumnField("NavigationEdge", "destination_node_id")
    accessible = ColumnField("NavigationEdge", "accessible")
    stairs = ColumnField("NavigationEdge", "stairs")

    def __init__(
        self,
        id: int = None,
        source_node_id: int = None,
        destination_node_id: int = None,
        distance: float = 0.0,
        accessible: bool = True,
        stairs: bool = False,
        path_type: str = "PAVED_WALKWAY",
        is_bidirectional: bool = True,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.source_node_id = int(source_node_id) if source_node_id is not None else None
        self.destination_node_id = int(destination_node_id) if destination_node_id is not None else None
        self.distance = float(distance)
        self.accessible = bool(accessible)
        self.stairs = bool(stairs)
        self.path_type = path_type or "PAVED_WALKWAY"
        self.is_bidirectional = bool(is_bidirectional)

        # Relationships
        self.source_node = None
        self.destination_node = None
        self.campus_id = None

    @classmethod
    def get(cls, edge_id: int):
        return data_store.get_by_id(cls, edge_id)

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

    def __repr__(self):
        return f"<NavigationEdge id={self.id} {self.source_node_id}->{self.destination_node_id} dist={self.distance}>"
