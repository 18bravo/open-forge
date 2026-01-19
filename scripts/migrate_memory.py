#!/usr/bin/env python3
"""
Memory Migration Script

Migrates existing custom memory implementation to LangGraph's PostgresStore format.
This script is part of WP3: LangGraph Memory Migration.

Usage:
    python scripts/migrate_memory.py [--dry-run] [--engagement-id ENG_ID]

Options:
    --dry-run           Preview migration without making changes
    --engagement-id     Migrate only a specific engagement
    --batch-size        Number of engagements to process per batch (default: 100)
    --verbose          Enable verbose logging
"""
import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add the packages to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'packages'))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryMigrator:
    """Handles migration from custom memory to LangGraph PostgresStore."""

    def __init__(
        self,
        connection_string: str,
        dry_run: bool = False,
        batch_size: int = 100
    ):
        """
        Initialize the migrator.

        Args:
            connection_string: Database connection string
            dry_run: If True, preview changes without applying them
            batch_size: Number of engagements to process per batch
        """
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            "engagements_processed": 0,
            "stakeholders_migrated": 0,
            "decisions_migrated": 0,
            "requirements_migrated": 0,
            "insights_migrated": 0,
            "errors": 0,
        }

        # Initialize database engine
        self.engine = create_async_engine(
            connection_string.replace("postgresql://", "postgresql+asyncpg://"),
            echo=False
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Initialize the new memory store (only if not dry run)
        self.store = None

    async def initialize_store(self):
        """Initialize the LangGraph PostgresStore."""
        if not self.dry_run:
            # Import here to avoid issues if LangGraph is not installed
            from agent_framework.memory.long_term import EngagementMemoryStore
            self.store = EngagementMemoryStore(self.connection_string)
            logger.info("Initialized EngagementMemoryStore")

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()

    async def get_engagements(
        self,
        engagement_id: Optional[str] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch engagements to migrate.

        Args:
            engagement_id: Optional specific engagement to fetch
            offset: Pagination offset

        Returns:
            List of engagement records with state
        """
        async with self.async_session() as session:
            if engagement_id:
                query = text("""
                    SELECT id, state, created_at, updated_at
                    FROM engagements.engagements
                    WHERE id = :engagement_id
                """)
                result = await session.execute(query, {"engagement_id": engagement_id})
            else:
                query = text("""
                    SELECT id, state, created_at, updated_at
                    FROM engagements.engagements
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                result = await session.execute(
                    query,
                    {"limit": self.batch_size, "offset": offset}
                )

            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "state": row[1] if isinstance(row[1], dict) else {},
                    "created_at": row[2],
                    "updated_at": row[3],
                }
                for row in rows
            ]

    async def get_agent_memories(
        self,
        engagement_id: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch existing agent memories for an engagement.

        Args:
            engagement_id: The engagement to fetch memories for

        Returns:
            List of memory records
        """
        async with self.async_session() as session:
            query = text("""
                SELECT id, agent_name, run_id, entry_type, content, timestamp
                FROM engagements.agent_memory
                WHERE engagement_id = :engagement_id
                ORDER BY timestamp ASC
            """)
            result = await session.execute(query, {"engagement_id": engagement_id})

            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "agent_name": row[1],
                    "run_id": row[2],
                    "entry_type": row[3],
                    "content": row[4] if isinstance(row[4], dict) else {},
                    "timestamp": row[5],
                }
                for row in rows
            ]

    async def migrate_engagement(self, engagement: Dict[str, Any]) -> Dict[str, int]:
        """
        Migrate a single engagement's memory to the new format.

        Args:
            engagement: The engagement record to migrate

        Returns:
            Dictionary of migration counts
        """
        engagement_id = engagement["id"]
        state = engagement.get("state", {})
        counts = {
            "stakeholders": 0,
            "decisions": 0,
            "requirements": 0,
            "insights": 0,
        }

        logger.info(f"Migrating engagement: {engagement_id}")

        # Migrate stakeholders from state
        stakeholders = state.get("stakeholders", [])
        for stakeholder in stakeholders:
            if self.dry_run:
                logger.debug(f"  [DRY RUN] Would migrate stakeholder: {stakeholder}")
            else:
                await self.store.store_memory(
                    engagement_id=engagement_id,
                    memory_type="stakeholder",
                    content=stakeholder if isinstance(stakeholder, dict) else {"name": stakeholder},
                    metadata={
                        "migrated_from": "state.stakeholders",
                        "migration_date": datetime.utcnow().isoformat(),
                    }
                )
            counts["stakeholders"] += 1

        # Migrate decisions from state
        decisions = state.get("agent_decisions", [])
        for decision in decisions:
            if self.dry_run:
                logger.debug(f"  [DRY RUN] Would migrate decision: {decision}")
            else:
                await self.store.store_memory(
                    engagement_id=engagement_id,
                    memory_type="decision",
                    content=decision if isinstance(decision, dict) else {"decision": decision},
                    metadata={
                        "migrated_from": "state.agent_decisions",
                        "migration_date": datetime.utcnow().isoformat(),
                    }
                )
            counts["decisions"] += 1

        # Migrate requirements/use_cases from state
        use_cases = state.get("use_cases", [])
        for use_case in use_cases:
            if self.dry_run:
                logger.debug(f"  [DRY RUN] Would migrate requirement: {use_case}")
            else:
                await self.store.store_memory(
                    engagement_id=engagement_id,
                    memory_type="requirement",
                    content=use_case if isinstance(use_case, dict) else {"requirement": use_case},
                    metadata={
                        "migrated_from": "state.use_cases",
                        "migration_date": datetime.utcnow().isoformat(),
                    }
                )
            counts["requirements"] += 1

        # Migrate agent memories (insights)
        agent_memories = await self.get_agent_memories(engagement_id)
        for memory in agent_memories:
            if memory.get("entry_type") == "insight":
                if self.dry_run:
                    logger.debug(f"  [DRY RUN] Would migrate insight: {memory['content']}")
                else:
                    await self.store.store_memory(
                        engagement_id=engagement_id,
                        memory_type="insight",
                        content=memory.get("content", {}),
                        metadata={
                            "migrated_from": "agent_memory",
                            "original_agent": memory.get("agent_name"),
                            "original_timestamp": memory.get("timestamp", "").isoformat() if memory.get("timestamp") else None,
                            "migration_date": datetime.utcnow().isoformat(),
                        }
                    )
                counts["insights"] += 1

        return counts

    async def run(self, engagement_id: Optional[str] = None):
        """
        Run the migration.

        Args:
            engagement_id: Optional specific engagement to migrate
        """
        logger.info("=" * 60)
        logger.info("Starting Memory Migration")
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        logger.info("=" * 60)

        await self.initialize_store()

        offset = 0
        while True:
            engagements = await self.get_engagements(
                engagement_id=engagement_id,
                offset=offset
            )

            if not engagements:
                break

            for engagement in engagements:
                try:
                    counts = await self.migrate_engagement(engagement)

                    self.stats["engagements_processed"] += 1
                    self.stats["stakeholders_migrated"] += counts["stakeholders"]
                    self.stats["decisions_migrated"] += counts["decisions"]
                    self.stats["requirements_migrated"] += counts["requirements"]
                    self.stats["insights_migrated"] += counts["insights"]

                    logger.info(
                        f"  Migrated: {counts['stakeholders']} stakeholders, "
                        f"{counts['decisions']} decisions, "
                        f"{counts['requirements']} requirements, "
                        f"{counts['insights']} insights"
                    )

                except Exception as e:
                    logger.error(f"Error migrating engagement {engagement['id']}: {e}")
                    self.stats["errors"] += 1

            # If we're migrating a specific engagement, stop after first batch
            if engagement_id:
                break

            offset += self.batch_size
            logger.info(f"Processed batch, offset now: {offset}")

        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Engagements processed: {self.stats['engagements_processed']}")
        logger.info(f"Stakeholders migrated: {self.stats['stakeholders_migrated']}")
        logger.info(f"Decisions migrated:    {self.stats['decisions_migrated']}")
        logger.info(f"Requirements migrated: {self.stats['requirements_migrated']}")
        logger.info(f"Insights migrated:     {self.stats['insights_migrated']}")
        logger.info(f"Errors:                {self.stats['errors']}")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("This was a DRY RUN. No changes were made.")
            logger.info("Run without --dry-run to apply changes.")


async def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate Open Forge memory to LangGraph PostgresStore"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes"
    )
    parser.add_argument(
        "--engagement-id",
        type=str,
        help="Migrate only a specific engagement"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of engagements to process per batch"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get connection string from environment
    connection_string = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/open_forge"
    )

    migrator = MemoryMigrator(
        connection_string=connection_string,
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )

    try:
        await migrator.run(engagement_id=args.engagement_id)
    finally:
        await migrator.close()


if __name__ == "__main__":
    asyncio.run(main())
