"""
Campus Navigation System — Spatial Types & Serialization Abstraction
Provides dialect-aware spatial types that map to PostGIS Geometry in PostgreSQL
and structured GeoJSON/WKT Text in SQLite/fallback environments.
"""
import json
from sqlalchemy.types import TypeDecorator, Text


class SpatialPoint(TypeDecorator):
    """Dialect-aware spatial Point (WGS84 EPSG:4326)."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from geoalchemy2 import Geometry
                return dialect.type_descriptor(Geometry("POINT", srid=4326))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # If string WKT "POINT(lng lat)" or tuple (lat, lng)
            if isinstance(value, (list, tuple)):
                return f"SRID=4326;POINT({value[1]} {value[0]})"
            return value
        # In SQLite / fallback, store as JSON [longitude, latitude]
        if isinstance(value, (list, tuple)):
            return json.dumps([float(value[1]), float(value[0])])
        if isinstance(value, dict):
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        try:
            return json.loads(value)
        except Exception:
            return value


class SpatialPolygon(TypeDecorator):
    """Dialect-aware spatial Polygon (WGS84 EPSG:4326)."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from geoalchemy2 import Geometry
                return dialect.type_descriptor(Geometry("POLYGON", srid=4326))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        try:
            return json.loads(value)
        except Exception:
            return value


class SpatialLineString(TypeDecorator):
    """Dialect-aware spatial LineString (WGS84 EPSG:4326)."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from geoalchemy2 import Geometry
                return dialect.type_descriptor(Geometry("LINESTRING", srid=4326))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        try:
            return json.loads(value)
        except Exception:
            return value
