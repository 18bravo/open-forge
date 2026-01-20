"""
Apache AGE graph database operations.
Provides Cypher query execution and graph management.
"""
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json


class CypherInjectionError(Exception):
    """Raised when a potential Cypher injection is detected."""
    pass


def _validate_identifier(identifier: str, identifier_type: str = "identifier") -> str:
    """
    Validate that an identifier is safe for use in Cypher/SQL.

    Args:
        identifier: The identifier to validate
        identifier_type: Type of identifier for error messages

    Returns:
        The validated identifier

    Raises:
        CypherInjectionError: If identifier contains unsafe characters
    """
    if not identifier:
        raise CypherInjectionError(f"{identifier_type} cannot be empty")

    # Only allow alphanumeric and underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise CypherInjectionError(
            f"Invalid {identifier_type} '{identifier}'. "
            "Must start with a letter or underscore and contain only "
            "alphanumeric characters and underscores."
        )

    if len(identifier) > 128:
        raise CypherInjectionError(f"{identifier_type} too long (max 128 chars)")

    return identifier


def _escape_cypher_string(value: str) -> str:
    """
    Escape a string value for safe use in Cypher queries.

    Escapes single quotes and backslashes.
    """
    # Escape backslashes first, then single quotes
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _format_cypher_value(value: Any) -> str:
    """
    Format a Python value for safe use in Cypher queries.

    Args:
        value: The value to format

    Returns:
        Cypher-safe string representation
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return f"'{_escape_cypher_string(value)}'"
    if isinstance(value, (list, tuple)):
        items = ", ".join(_format_cypher_value(item) for item in value)
        return f"[{items}]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{_validate_identifier(k, 'property name')}: {_format_cypher_value(v)}"
            for k, v in value.items()
        )
        return f"{{{items}}}"
    # Fallback - convert to string and escape
    return f"'{_escape_cypher_string(str(value))}'"


class GraphDatabase:
    """Apache AGE graph database interface."""

    def __init__(self, graph_name: str = "ontology_graph"):
        self.graph_name = _validate_identifier(graph_name, "graph name")

    async def initialize(self, session: AsyncSession) -> None:
        """Initialize the graph database."""
        # Load AGE extension
        await session.execute(text("LOAD 'age'"))
        await session.execute(text("SET search_path = ag_catalog, \"$user\", public"))

        # Create graph if not exists - using parameterized query
        result = await session.execute(
            text("SELECT * FROM ag_catalog.ag_graph WHERE name = :graph_name"),
            {"graph_name": self.graph_name}
        )
        if not result.fetchone():
            # Graph name is validated in __init__, safe to use in query
            await session.execute(text(f"SELECT create_graph('{self.graph_name}')"))

    async def execute_cypher(
        self,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Execute a Cypher query and return results.

        Note: Apache AGE doesn't support native query parameters in Cypher,
        so values are escaped and sanitized before interpolation.
        """
        # Build the Cypher query with safely escaped parameters
        cypher_query = query
        if params:
            for key, value in params.items():
                _validate_identifier(key, "parameter name")
                safe_value = _format_cypher_value(value)
                cypher_query = cypher_query.replace(f"${key}", safe_value)

        # Graph name is validated in __init__
        sql = f"""
        SELECT * FROM cypher('{self.graph_name}', $$
            {cypher_query}
        $$) as (result agtype)
        """

        result = await session.execute(text(sql))
        rows = result.fetchall()

        # Parse agtype results to Python objects
        return [self._parse_agtype(row[0]) for row in rows]
    
    async def create_node(
        self,
        session: AsyncSession,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict:
        """Create a node in the graph."""
        safe_label = _validate_identifier(label, "node label")
        props_str = _format_cypher_value(properties)
        query = f"CREATE (n:{safe_label} {props_str}) RETURN n"
        results = await self.execute_cypher(session, query)
        return results[0] if results else None

    async def create_edge(
        self,
        session: AsyncSession,
        edge_type: str,
        from_label: str,
        from_key: str,
        from_value: Any,
        to_label: str,
        to_key: str,
        to_value: Any,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Create an edge between two nodes."""
        # Validate all identifiers
        safe_edge_type = _validate_identifier(edge_type, "edge type")
        safe_from_label = _validate_identifier(from_label, "from label")
        safe_from_key = _validate_identifier(from_key, "from key")
        safe_to_label = _validate_identifier(to_label, "to label")
        safe_to_key = _validate_identifier(to_key, "to key")

        props_str = _format_cypher_value(properties) if properties else "{}"

        query = f"""
        MATCH (a:{safe_from_label} {{{safe_from_key}: $from_value}}),
              (b:{safe_to_label} {{{safe_to_key}: $to_value}})
        CREATE (a)-[r:{safe_edge_type} {props_str}]->(b)
        RETURN r
        """

        results = await self.execute_cypher(session, query, {
            "from_value": from_value,
            "to_value": to_value
        })
        return results[0] if results else None

    async def upsert_node(
        self,
        session: AsyncSession,
        label: str,
        key_property: str,
        properties: Dict[str, Any]
    ) -> Dict:
        """Upsert a node (create or update)."""
        safe_label = _validate_identifier(label, "node label")
        safe_key_prop = _validate_identifier(key_property, "key property")

        key_value = properties[key_property]
        props_str = _format_cypher_value(properties)

        query = f"""
        MERGE (n:{safe_label} {{{safe_key_prop}: $key_value}})
        SET n = {props_str}
        RETURN n
        """

        results = await self.execute_cypher(session, query, {"key_value": key_value})
        return results[0] if results else None
    
    def _parse_agtype(self, agtype_value: str) -> Any:
        """Parse AGE agtype value to Python object."""
        if agtype_value is None:
            return None
        # AGE returns JSON-like strings
        try:
            return json.loads(str(agtype_value))
        except json.JSONDecodeError:
            return str(agtype_value)