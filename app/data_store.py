"""
Campus Navigation System — In-Memory Data Store
Provides a lightweight, zero-database data store backed by static JSON files.
Supports in-memory indexing, query abstractions, relationship navigation, and mutations.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("campus_nav.data_store")

DATA_DIR = Path(__file__).resolve().parent / "data"


class ColumnField:
    """Descriptor enabling in-memory field filters and sort specifications."""
    def __init__(self, model_name: str, field_name: str):
        self.model_name = model_name
        self.field_name = field_name

    def __eq__(self, other):
        def pred(item):
            # 1. Direct class match
            if item.__class__.__name__ == self.model_name:
                val = getattr(item, self.field_name, None)
                return val == other
            # 2. Relationship match (e.g., room.building.campus_id == other)
            rel_attr = self.model_name.lower()
            if hasattr(item, rel_attr):
                rel = getattr(item, rel_attr)
                if rel is not None:
                    return getattr(rel, self.field_name, None) == other
            # 3. Source node match for navigation edge (e.g., edge.source_node.campus_id == other)
            if hasattr(item, "source_node"):
                src = getattr(item, "source_node")
                if src is not None:
                    return getattr(src, self.field_name, None) == other
            # 4. Fallback
            return getattr(item, self.field_name, None) == other
        return pred

    def __ne__(self, other):
        eq_pred = self.__eq__(other)
        return lambda item: not eq_pred(item)

    def in_(self, values):
        def pred(item):
            val = getattr(item, self.field_name, None)
            return val in values
        return pred

    def desc(self):
        return (self.field_name, True)

    def asc(self):
        return (self.field_name, False)


class Query:
    """Small in-memory query helper used by the data-backed models."""
    def __init__(self, items: List[Any], model_cls: Any = None):
        self._items = list(items)
        self._model_cls = model_cls

    def all(self) -> List[Any]:
        return list(self._items)

    def first(self) -> Optional[Any]:
        return self._items[0] if self._items else None

    def count(self) -> int:
        return len(self._items)

    def filter_by(self, **kwargs) -> "Query":
        filtered = []
        for item in self._items:
            match = True
            for k, v in kwargs.items():
                attr_val = getattr(item, k, None)
                if attr_val != v:
                    match = False
                    break
            if match:
                filtered.append(item)
        return Query(filtered, self._model_cls)

    def filter(self, *criteria) -> "Query":
        filtered = self._items
        for criterion in criteria:
            if callable(criterion):
                filtered = [item for item in filtered if criterion(item)]
        return Query(filtered, self._model_cls)

    def join(self, target_model, *args, **kwargs) -> "Query":
        # In-memory relationships are already wired; return self
        return self

    def order_by(self, *order_specs) -> "Query":
        items = list(self._items)
        for spec in reversed(order_specs):
            if isinstance(spec, tuple):
                field_name, descending = spec
                items.sort(key=lambda x: str(getattr(x, field_name, "") or ""), reverse=descending)
            elif isinstance(spec, str):
                descending = spec.startswith("-")
                field_name = spec.lstrip("-")
                items.sort(key=lambda x: str(getattr(x, field_name, "") or ""), reverse=descending)
        return Query(items, self._model_cls)

    def limit(self, n: int) -> "Query":
        return Query(self._items[:n], self._model_cls)

    def offset(self, n: int) -> "Query":
        return Query(self._items[n:], self._model_cls)

    def delete(self, synchronize_session=False):
        for item in list(self._items):
            data_store.delete(item)
        self._items = []

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]


class DataStore:
    """Central repository storing all campus navigation entities in memory."""
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self._campuses: Dict[int, Any] = {}
        self._categories: Dict[int, Any] = {}
        self._buildings: Dict[int, Any] = {}
        self._rooms: Dict[int, Any] = {}
        self._facilities: Dict[int, Any] = {}
        self._navigation_nodes: Dict[int, Any] = {}
        self._navigation_edges: Dict[int, Any] = {}
        self._admin_users: Dict[int, Any] = {}
        self._audit_logs: Dict[int, Any] = {}
        self._initialized = False

    def init_app(self, app=None):
        """Initialize data store from configured DATA_DIR or default."""
        if app and "DATA_DIR" in app.config:
            self.data_dir = Path(app.config["DATA_DIR"])
        self.load()

    def is_ready(self) -> bool:
        return self._initialized and len(self._campuses) > 0

    def load(self):
        """Loads all static JSON files and wires entity relationships."""
        from app.models.campus import Campus
        from app.models.category import Category
        from app.models.building import Building
        from app.models.room import Room
        from app.models.facility import Facility
        from app.models.navigation import NavigationNode, NavigationEdge
        from app.models.admin import AdminUser
        from app.models.audit import AuditLog

        self.clear()

        # 1. Campuses
        campuses_path = self.data_dir / "campuses.json"
        if campuses_path.exists():
            with open(campuses_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    c = Campus(**item)
                    self._campuses[c.id] = c

        # 2. Categories
        categories_path = self.data_dir / "categories.json"
        if categories_path.exists():
            with open(categories_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    cat = Category(**item)
                    self._categories[cat.id] = cat

        # 3. Buildings
        buildings_path = self.data_dir / "buildings.json"
        if buildings_path.exists():
            with open(buildings_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    b = Building(**item)
                    self._buildings[b.id] = b

        # 4. Rooms
        rooms_path = self.data_dir / "rooms.json"
        if rooms_path.exists():
            with open(rooms_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    r = Room(**item)
                    self._rooms[r.id] = r

        # 5. Facilities
        facilities_path = self.data_dir / "facilities.json"
        if facilities_path.exists():
            with open(facilities_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    fac = Facility(**item)
                    self._facilities[fac.id] = fac

        # 6. Navigation Networks (SVCE + Demo)
        for net_file in ["svce_network.json", "demo_network.json"]:
            net_path = self.data_dir / net_file
            if net_path.exists():
                with open(net_path, "r", encoding="utf-8") as f:
                    net_data = json.load(f)
                    for n_data in net_data.get("nodes", []):
                        node = NavigationNode(**n_data)
                        self._navigation_nodes[node.id] = node
                    for e_data in net_data.get("edges", []):
                        edge = NavigationEdge(**e_data)
                        self._navigation_edges[edge.id] = edge

        # 7. Admin Users
        admins_path = self.data_dir / "admins.json"
        if admins_path.exists():
            with open(admins_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    u = AdminUser(**item)
                    self._admin_users[u.id] = u

        # Wire bi-directional relationships
        self._wire_relationships()
        self._initialized = True
        logger.info(
            f"DataStore initialized with {len(self._campuses)} campuses, "
            f"{len(self._buildings)} buildings, {len(self._rooms)} rooms, "
            f"{len(self._facilities)} facilities, {len(self._navigation_nodes)} nodes, "
            f"{len(self._navigation_edges)} edges."
        )

    def _wire_relationships(self):
        """Connect cross-entity object references."""
        # Reset collections
        for c in self._campuses.values():
            c.buildings = []
            c.facilities = []
            c.navigation_nodes = []

        for b in self._buildings.values():
            b.rooms = []
            b.facilities = []
            b.navigation_nodes = []
            b.campus = self._campuses.get(b.campus_id)
            if b.campus:
                b.campus.buildings.append(b)

        for cat in self._categories.values():
            cat.facilities = []

        for f in self._facilities.values():
            f.campus = self._campuses.get(f.campus_id)
            if f.campus:
                f.campus.facilities.append(f)
            f.building = self._buildings.get(f.building_id) if f.building_id else None
            if f.building:
                f.building.facilities.append(f)
            f.category = self._categories.get(f.category_id) if f.category_id else None
            if f.category:
                f.category.facilities.append(f)

        for r in self._rooms.values():
            r.building = self._buildings.get(r.building_id)
            if r.building:
                r.building.rooms.append(r)
            r.door_node = self._navigation_nodes.get(r.node_id) if r.node_id else None

        for n in self._navigation_nodes.values():
            n.campus = self._campuses.get(n.campus_id)
            if n.campus:
                n.campus.navigation_nodes.append(n)
            n.building = self._buildings.get(n.building_id) if n.building_id else None
            if n.building:
                n.building.navigation_nodes.append(n)
            n.outgoing_edges = []
            n.incoming_edges = []

        for e in self._navigation_edges.values():
            src = self._navigation_nodes.get(e.source_node_id)
            dst = self._navigation_nodes.get(e.destination_node_id)
            e.source_node = src
            e.destination_node = dst
            e.campus_id = src.campus_id if src else (dst.campus_id if dst else None)
            if src:
                src.outgoing_edges.append(e)
            if dst:
                dst.incoming_edges.append(e)

        for log in self._audit_logs.values():
            log.admin = self._admin_users.get(log.admin_id) if log.admin_id else None

    def clear(self):
        self._campuses.clear()
        self._categories.clear()
        self._buildings.clear()
        self._rooms.clear()
        self._facilities.clear()
        self._navigation_nodes.clear()
        self._navigation_edges.clear()
        self._admin_users.clear()
        self._audit_logs.clear()
        self._initialized = False

    def reset(self):
        self.load()

    # Query & Access Helpers
    def get_query(self, model_cls) -> Query:
        name = model_cls.__name__
        mapping = {
            "Campus": self._campuses,
            "Category": self._categories,
            "Building": self._buildings,
            "Room": self._rooms,
            "Facility": self._facilities,
            "NavigationNode": self._navigation_nodes,
            "NavigationEdge": self._navigation_edges,
            "AdminUser": self._admin_users,
            "AuditLog": self._audit_logs,
        }
        target_dict = mapping.get(name, {})
        return Query(list(target_dict.values()), model_cls)

    def get_by_id(self, model_cls, entity_id: int):
        name = model_cls.__name__ if hasattr(model_cls, "__name__") else str(model_cls)
        mapping = {
            "Campus": self._campuses,
            "Category": self._categories,
            "Building": self._buildings,
            "Room": self._rooms,
            "Facility": self._facilities,
            "NavigationNode": self._navigation_nodes,
            "NavigationEdge": self._navigation_edges,
            "AdminUser": self._admin_users,
            "AuditLog": self._audit_logs,
        }
        target_dict = mapping.get(name, {})
        try:
            return target_dict.get(int(entity_id))
        except (ValueError, TypeError):
            return None

    def add(self, entity):
        """Add or update entity in memory."""
        name = entity.__class__.__name__
        mapping = {
            "Campus": self._campuses,
            "Category": self._categories,
            "Building": self._buildings,
            "Room": self._rooms,
            "Facility": self._facilities,
            "NavigationNode": self._navigation_nodes,
            "NavigationEdge": self._navigation_edges,
            "AdminUser": self._admin_users,
            "AuditLog": self._audit_logs,
        }
        target_dict = mapping.get(name)
        if target_dict is not None:
            if getattr(entity, "id", None) is None:
                new_id = max(target_dict.keys(), default=0) + 1
                entity.id = new_id
            target_dict[entity.id] = entity
            self._wire_relationships()

    def delete(self, entity):
        """Delete entity from memory."""
        name = entity.__class__.__name__
        mapping = {
            "Campus": self._campuses,
            "Category": self._categories,
            "Building": self._buildings,
            "Room": self._rooms,
            "Facility": self._facilities,
            "NavigationNode": self._navigation_nodes,
            "NavigationEdge": self._navigation_edges,
            "AdminUser": self._admin_users,
            "AuditLog": self._audit_logs,
        }
        target_dict = mapping.get(name)
        if target_dict is not None and getattr(entity, "id", None) in target_dict:
            del target_dict[entity.id]
            self._wire_relationships()


# Global Singleton DataStore instance
data_store = DataStore()
