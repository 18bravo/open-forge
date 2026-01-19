"""
Open Forge API Package

FastAPI-based REST and GraphQL API.
"""

__version__ = "0.1.0"


def get_app():
    """Get the FastAPI application instance."""
    from api.main import app
    return app


__all__ = ["__version__", "get_app"]
