"""
Campus Navigation System — CLI Tooling
Database-free: commands for inspecting and validating static JSON datasets.
"""
import click
from app.data_store import data_store


def register_commands(app):
    """Register CLI commands with Flask application."""

    @app.cli.command("validate-data")
    def validate_data_command():
        """Validate all static JSON files in app/data."""
        data_store.load()
        click.echo("✓ Static JSON datasets validated successfully:")
        click.echo(f"  • Campuses: {len(data_store._campuses)}")
        click.echo(f"  • Categories: {len(data_store._categories)}")
        click.echo(f"  • Buildings: {len(data_store._buildings)}")
        click.echo(f"  • Rooms: {len(data_store._rooms)}")
        click.echo(f"  • Facilities: {len(data_store._facilities)}")
        click.echo(f"  • Navigation Nodes: {len(data_store._navigation_nodes)}")
        click.echo(f"  • Navigation Edges: {len(data_store._navigation_edges)}")
