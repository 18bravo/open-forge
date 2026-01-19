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
    ) -> Dict:
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
    ) -> Dict:
        """Create an edge between two nodes."""
        props_str = json.dumps(properties) if properties else "{}"
        
        query = f"""
        MATCH (a:{from_label} {{{from_key}: $from_value}}),
              (b:{to_label} {{{to_key}: $to_value}})
        CREATE (a)-[r:{edge_type} {props_str}]->(b)
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
        key_value = properties[key_property]
        props_str = json.dumps(properties)
        
        query = f"""
        MERGE (n:{label} {{{key_property}: $key_value}})
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