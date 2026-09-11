"""
Campus Navigation System — Admin Web Views
Handles admin login sessions and the administrative spatial management dashboard.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.admin import AdminUser
from app.models.audit import AuditLog
from app.models.campus import Campus
from app.models.building import Building
from app.models.facility import Facility
from app.models.category import Category
from app.models.navigation import NavigationNode, NavigationEdge
from app.utils.security import verify_password, login_admin, logout_admin, admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if "admin_id" in session:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = AdminUser.query.filter_by(username=username, is_active=True).first()
        if user and verify_password(password, user.password_hash):
            login_admin({"id": user.id, "username": user.username, "role": user.role})
            next_url = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_url)
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Admin logout."""
    logout_admin()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def dashboard():
    """Administrative dashboard showing campus topology and audit trails."""
    campuses = Campus.query.all()
    buildings = Building.query.all()
    facilities = Facility.query.all()
    categories = Category.query.all()
    node_count = NavigationNode.query.count()
    edge_count = NavigationEdge.query.count()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()

    return render_template(
        "admin/dashboard.html",
        campuses=campuses,
        buildings=buildings,
        facilities=facilities,
        categories=categories,
        node_count=node_count,
        edge_count=edge_count,
        recent_logs=recent_logs,
        admin_username=session.get("admin_username")
    )
