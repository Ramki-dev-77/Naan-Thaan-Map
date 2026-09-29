"""
Campus Navigation System — Audit Log Model
Immutable event log recording administrative operations.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
import json
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class AuditLog(metaclass=_ModelMeta):
    id = ColumnField("AuditLog", "id")
    admin_id = ColumnField("AuditLog", "admin_id")
    action = ColumnField("AuditLog", "action")
    created_at = ColumnField("AuditLog", "created_at")

    def __init__(
        self,
        id: int = None,
        admin_id: int = None,
        action: str = "",
        entity_type: str = "",
        entity_id: int = None,
        metadata_json: str = None,
        ip_address: str = None,
        created_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.admin_id = int(admin_id) if admin_id is not None else None
        self.action = action
        self.entity_type = entity_type
        self.entity_id = int(entity_id) if entity_id is not None else None
        self.metadata_json = metadata_json
        self.ip_address = ip_address
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.admin = None

    @classmethod
    def get(cls, log_id: int):
        return data_store.get_by_id(cls, log_id)

    def to_dict(self):
        meta = None
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                meta = self.metadata_json

        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_username": self.admin.username if self.admin else "System",
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metadata": meta,
            "ip_address": self.ip_address,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f"<AuditLog id={self.id} action='{self.action}'>"
