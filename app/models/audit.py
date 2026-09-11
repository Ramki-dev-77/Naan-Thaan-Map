"""
Campus Navigation System — Audit Log Model
Immutable event log recording all state-changing administrative operations.
"""
from datetime import datetime, timezone
import json
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)  # e.g., 'CREATE_BUILDING', 'UPDATE_NODE'
    entity_type = db.Column(db.String(50), nullable=False, index=True) # e.g., 'Building', 'Room', 'NavigationEdge'
    entity_id = db.Column(db.Integer, nullable=True)
    
    # JSON metadata payload (stored as Text for SQLite / JSONB in PostgreSQL)
    metadata_json = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    admin = db.relationship("AdminUser", back_populates="audit_logs")

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
