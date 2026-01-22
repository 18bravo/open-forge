"""
Connector registry for plugin-based discovery.

The registry provides:
- Registration of connector classes via decorator
- Auto-discovery of connectors via entry points
- Lookup by connector type
- Listing of all available connectors
"""

import importlib.metadata
import logging
from dataclasses import dataclass, field
from typing import Type

from forge_connectors.core.base import BaseConnector, ConnectorCapability

logger = logging.getLogger(__name__)


class ConnectorNotFoundError(Exception):
    """Raised when a requested connector type is not registered."""

    pass


@dataclass
class ConnectorInfo:
    """Information about a registered connector."""

    connector_type: str
    category: str
    capabilities: list[ConnectorCapability]
    description: str = ""
    connector_class: Type[BaseConnector] | None = field(default=None, repr=False)


class ConnectorRegistry:
    """
    Central registry for all connector plugins.

    Connectors register themselves using the @register decorator or via entry points.
    The registry provides lookup and discovery functionality.

    Example:
        @ConnectorRegistry.register('postgresql', 'sql')
        class PostgreSQLConnector(BaseConnector):
            ...

        # Get a connector class
        cls = ConnectorRegistry.get('postgresql')

        # List all connectors
        for info in ConnectorRegistry.list_all():
            print(f"{info.connector_type}: {info.capabilities}")
    """

    _connectors: dict[str, Type[BaseConnector]] = {}
    _categories: dict[str, list[str]] = {}
    _discovered: bool = False

    @classmethod
    def register(cls, connector_type: str, category: str, description: str = ""):
        """
        Decorator to register a connector class.

        Args:
            connector_type: Unique identifier (e.g., 'postgresql')
            category: Category (e.g., 'sql', 'warehouse', 'streaming', 'api')
            description: Optional human-readable description

        Returns:
            Decorator function

        Example:
            @ConnectorRegistry.register('postgresql', 'sql', 'PostgreSQL database')
            class PostgreSQLConnector(BaseConnector):
                ...
        """

        def decorator(connector_class: Type[BaseConnector]) -> Type[BaseConnector]:
            # Set class attributes
            connector_class.connector_type = connector_type
            connector_class.category = category

            # Register in the registry
            cls._connectors[connector_type] = connector_class
            cls._categories.setdefault(category, []).append(connector_type)

            logger.debug(f"Registered connector: {connector_type} (category: {category})")

            return connector_class

        return decorator

    @classmethod
    def get(cls, connector_type: str) -> Type[BaseConnector]:
        """
        Get a connector class by type.

        Args:
            connector_type: The connector type identifier.

        Returns:
            The connector class.

        Raises:
            ConnectorNotFoundError: If connector type is not registered.
        """
        # Ensure plugins are discovered
        if not cls._discovered:
            cls.discover_plugins()

        if connector_type not in cls._connectors:
            available = ", ".join(sorted(cls._connectors.keys()))
            raise ConnectorNotFoundError(
                f"Unknown connector type: '{connector_type}'. "
                f"Available: {available or 'none (run discover_plugins first)'}"
            )

        return cls._connectors[connector_type]

    @classmethod
    def list_all(cls) -> list[ConnectorInfo]:
        """
        List all registered connectors.

        Returns:
            List of ConnectorInfo objects.
        """
        # Ensure plugins are discovered
        if not cls._discovered:
            cls.discover_plugins()

        return [
            ConnectorInfo(
                connector_type=ct,
                category=cc.category,
                capabilities=cc.get_capabilities(),
                description=cc.__doc__.split("\n")[0] if cc.__doc__ else "",
                connector_class=cc,
            )
            for ct, cc in sorted(cls._connectors.items())
        ]

    @classmethod
    def list_by_category(cls, category: str) -> list[ConnectorInfo]:
        """
        List connectors in a specific category.

        Args:
            category: Category to filter by (e.g., 'sql', 'warehouse')

        Returns:
            List of ConnectorInfo for connectors in that category.
        """
        # Ensure plugins are discovered
        if not cls._discovered:
            cls.discover_plugins()

        connector_types = cls._categories.get(category, [])
        return [
            ConnectorInfo(
                connector_type=ct,
                category=category,
                capabilities=cls._connectors[ct].get_capabilities(),
                description=cls._connectors[ct].__doc__.split("\n")[0]
                if cls._connectors[ct].__doc__
                else "",
                connector_class=cls._connectors[ct],
            )
            for ct in sorted(connector_types)
        ]

    @classmethod
    def get_categories(cls) -> list[str]:
        """
        Get list of all connector categories.

        Returns:
            List of category names.
        """
        if not cls._discovered:
            cls.discover_plugins()

        return sorted(cls._categories.keys())

    @classmethod
    def discover_plugins(cls) -> int:
        """
        Auto-discover connectors via entry points.

        Looks for entry points in the 'forge.connectors' group.
        Each entry point should point to a connector class decorated with @register.

        Returns:
            Number of connectors discovered.
        """
        if cls._discovered:
            return len(cls._connectors)

        count = 0
        try:
            entry_points = importlib.metadata.entry_points(group="forge.connectors")
            for ep in entry_points:
                try:
                    # Loading the entry point triggers the @register decorator
                    ep.load()
                    count += 1
                    logger.debug(f"Discovered connector via entry point: {ep.name}")
                except Exception as e:
                    logger.warning(f"Failed to load connector entry point '{ep.name}': {e}")
        except Exception as e:
            logger.warning(f"Failed to enumerate connector entry points: {e}")

        cls._discovered = True
        logger.info(f"Discovered {count} connector(s) via entry points")
        return count

    @classmethod
    def is_registered(cls, connector_type: str) -> bool:
        """
        Check if a connector type is registered.

        Args:
            connector_type: The connector type to check.

        Returns:
            True if registered, False otherwise.
        """
        if not cls._discovered:
            cls.discover_plugins()

        return connector_type in cls._connectors

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered connectors (useful for testing).
        """
        cls._connectors.clear()
        cls._categories.clear()
        cls._discovered = False
