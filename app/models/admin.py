"""
Campus Navigation System — Administrator User Model
Manages authenticated access with hashed credentials and roles.
Zero-database in-memory model backed by data_store.
"""
from datetime import datetime, timezone
from app.data_store import data_store, ColumnField


class _ModelMeta(type):
    @property
    def query(cls):
        return data_store.get_query(cls)


class AdminUser(metaclass=_ModelMeta):
    id = ColumnField("AdminUser", "id")
    username = ColumnField("AdminUser", "username")
    email = ColumnField("AdminUser", "email")
    role = ColumnField("AdminUser", "role")
    is_active = ColumnField("AdminUser", "is_active")

    def __init__(
        self,
        id: int = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
        role: str = "admin",
        is_active: bool = True,
        last_login: str = None,
        created_at: str = None,
        **kwargs
    ):
        self.id = int(id) if id is not None else None
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active = bool(is_active)
        self.last_login = last_login
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.audit_logs = []

    @classmethod
    def get(cls, user_id: int):
        return data_store.get_by_id(cls, user_id)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f"<AdminUser id={self.id} username='{self.username}'>"
