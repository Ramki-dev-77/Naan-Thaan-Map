"""
Campus Navigation System — Category Model
Provides taxonomical grouping (Academic, Dining, Parking, Restrooms, Health, etc.)
with icons and UI badges.
"""
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(50), nullable=False, default="map-pin")  # e.g., 'utensils', 'book', 'car', 'first-aid'
    color = db.Column(db.String(30), nullable=False, default="#2563eb")  # Hex color code

    facilities = db.relationship("Facility", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "icon": self.icon,
            "color": self.color,
        }
