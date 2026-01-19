"""
Apache AGE graph database operations.
Provides Cypher query execution and graph management.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json


class GraphDatabase:
    """Apache AGE graph database interface."""

    def __init__(self, graph_name: str = "ontology_graph"):
        self.graph_name = graph_name

    async def initialize(self, session: AsyncSession) -> None:
        """Initialize the graph database."""
        # Load AGE extension
        await session.execute(text("LOAD 'age'"))
        await session.execute(text("SET search_path = ag_catalog, \"$user\", public"))

        # Create graph if not exists
        result = await session.execute(text(
            f"SELECT * FROM ag_catalog.ag_graph WHERE name = '{self.graph_name}'"
        ))
        if not result.fetchone():
            await session.execute(text(f"SELECT create_graph('{self.graph_name}')"))
        await session.commit()

    async def execute_cypher(
        self,
        session: AsyncSession,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute a Cypher query and return results."""
        # Build the SQL wrapper for Cypher
        cypher_query = query
        if params:
            for key, value in params.items():
                if isinstance(value, str):
                    cypher_query = cypher_query.replace(f"${key}", f"'{value}'")
                else:
                    cypher_query = cypher_query.replace(f"${key}", str(value))

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
    ) -> Optional[Dict]:
        """Create a node in the graph."""
        props_str = json.dumps(properties)
        query = f"CREATE (n:{label} {props_str}) RETURN n"
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
    ) -> Optional[Dict]:
        """Create an edge between two nodes."""
        props_str = json.dumps(properties) if properties else "{}"

        # Build match criteria
        from_match = f"{{{from_key}: '{from_value}'}}" if isinstance(from_value, str) else f"{{{from_key}: {from_value}}}"
        to_match = f"{{{to_key}: '{to_value}'}}" if isinstance(to_value, str) else f"{{{to_key}: {to_value}}}"

        query = f"""
        MATCH (a:{from_label} {from_match}),
              (b:{to_label} {to_match})
        CREATE (a)-[r:{edge_type} {props_str}]->(b)
        RETURN r
        """

        results = await self.execute_cypher(session, query)
        return results[0] if results else None

    async def upsert_node(
        self,
        session: AsyncSession,
        label: str,
        key_property: str,
        properties: Dict[str, Any]
    ) -> Optional[Dict]:
        """Upsert a node (create or update)."""
        key_value = properties[key_property]
        props_str = json.dumps(properties)

        # Build key match
        key_match = f"'{key_value}'" if isinstance(key_value, str) else str(key_value)

        query = f"""
        MERGE (n:{label} {{{key_property}: {key_match}}})
        SET n = {props_str}
        RETURN n
        """

        results = await self.execute_cypher(session, query)
        return results[0] if results else None

    async def find_node(
        self,
        session: AsyncSession,
        label: str,
        properties: Dict[str, Any]
    ) -> List[Dict]:
        """Find nodes matching properties."""
        match_parts = []
        for key, value in properties.items():
            if isinstance(value, str):
                match_parts.append(f"{key}: '{value}'")
            else:
                match_parts.append(f"{key}: {value}")
        match_str = ", ".join(match_parts)

        query = f"MATCH (n:{label} {{{match_str}}}) RETURN n"
        return await self.execute_cypher(session, query)

    async def find_connected(
        self,
        session: AsyncSession,
        from_label: str,
        from_key: str,
        from_value: Any,
        edge_type: str,
        to_label: str
    ) -> List[Dict]:
        """Find nodes connected to a given node."""
        from_match = f"'{from_value}'" if isinstance(from_value, str) else str(from_value)

        query = f"""
        MATCH (a:{from_label} {{{from_key}: {from_match}}})-[r:{edge_type}]->(b:{to_label})
        RETURN b, r
        """
        return await self.execute_cypher(session, query)

    async def delete_node(
        self,
        session: AsyncSession,
        label: str,
        key_property: str,
        key_value: Any
    ) -> bool:
        """Delete a node and its relationships."""
        key_match = f"'{key_value}'" if isinstance(key_value, str) else str(key_value)

        query = f"""
        MATCH (n:{label} {{{key_property}: {key_match}}})
        DETACH DELETE n
        """
        await self.execute_cypher(session, query)
        return True

    def _parse_agtype(self, agtype_value: Any) -> Any:
        """Parse AGE agtype value to Python object."""
        if agtype_value is None:
            return None
        # AGE returns JSON-like strings
        try:
            if isinstance(agtype_value, str):
                return json.loads(agtype_value)
            return agtype_value
        except json.JSONDecodeError:
            return str(agtype_value)
