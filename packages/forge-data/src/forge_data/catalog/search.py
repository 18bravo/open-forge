"""
Catalog search functionality.

Provides full-text and metadata search across the data catalog.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from forge_data.catalog.navigator import AssetType, DataAsset


class SortField(str, Enum):
    """Fields available for sorting search results."""

    RELEVANCE = "relevance"
    NAME = "name"
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
    POPULARITY = "popularity"


class SortOrder(str, Enum):
    """Sort order."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class SearchFilter:
    """
    Filters for catalog search.

    All filters are optional and combined with AND logic.
    """

    # Type filters
    asset_types: list[AssetType] | None = None
    source_systems: list[str] | None = None

    # Ownership filters
    owner_ids: list[str] | None = None
    team_ids: list[str] | None = None

    # Tag filters
    tags: list[str] | None = None  # Match any tag key or value
    tag_keys: list[str] | None = None  # Match specific tag keys

    # Classification
    classifications: list[str] | None = None

    # Date filters
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None

    # Quality filters
    min_quality_score: float | None = None

    # Include/exclude
    include_deprecated: bool = False
    include_deleted: bool = False


@dataclass
class SearchResult:
    """
    A single search result with relevance scoring.
    """

    asset: DataAsset
    score: float  # Relevance score 0-1
    highlights: dict[str, list[str]] = field(default_factory=dict)  # Field -> highlighted snippets
    matched_fields: list[str] = field(default_factory=list)


@dataclass
class SearchResponse:
    """
    Response from a catalog search.
    """

    results: list[SearchResult]
    total_count: int
    page: int
    page_size: int
    query: str
    filters_applied: SearchFilter | None = None
    execution_ms: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results."""
        return (self.page * self.page_size) < self.total_count


class CatalogSearch:
    """
    Search engine for the data catalog.

    Provides full-text search across asset names, descriptions,
    columns, and metadata with filtering and relevance scoring.

    Example:
        search = CatalogSearch(navigator)

        # Simple search
        results = await search.search("customer orders")

        # Search with filters
        results = await search.search(
            query="revenue",
            filters=SearchFilter(
                asset_types=[AssetType.TABLE],
                source_systems=["snowflake"]
            ),
            sort_by=SortField.POPULARITY
        )

        # Browse by tag
        results = await search.search_by_tag("pii")
    """

    def __init__(self, navigator: "CatalogNavigator"):
        """
        Initialize catalog search.

        Args:
            navigator: Catalog navigator instance
        """
        self.navigator = navigator

    async def search(
        self,
        query: str,
        filters: SearchFilter | None = None,
        sort_by: SortField = SortField.RELEVANCE,
        sort_order: SortOrder = SortOrder.DESC,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """
        Search the catalog.

        Args:
            query: Search query string
            filters: Optional filters
            sort_by: Sort field
            sort_order: Sort order
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            SearchResponse with results
        """
        start_time = datetime.utcnow()

        # Get all assets (in production, would use proper search index)
        assets = await self.navigator.list_assets(limit=10000)

        # Filter assets
        if filters:
            assets = self._apply_filters(assets, filters)

        # Score and rank by query relevance
        scored_results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for asset in assets:
            score, highlights, matched_fields = self._calculate_relevance(
                asset, query_terms
            )

            if score > 0:
                scored_results.append(
                    SearchResult(
                        asset=asset,
                        score=score,
                        highlights=highlights,
                        matched_fields=matched_fields,
                    )
                )

        # Sort results
        scored_results = self._sort_results(scored_results, sort_by, sort_order)

        # Paginate
        total_count = len(scored_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = scored_results[start_idx:end_idx]

        execution_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return SearchResponse(
            results=page_results,
            total_count=total_count,
            page=page,
            page_size=page_size,
            query=query,
            filters_applied=filters,
            execution_ms=execution_ms,
        )

    async def search_by_tag(
        self,
        tag: str,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """
        Search for assets with a specific tag.

        Args:
            tag: Tag key or value to search for
            page: Page number
            page_size: Results per page

        Returns:
            SearchResponse with tagged assets
        """
        return await self.search(
            query="",
            filters=SearchFilter(tags=[tag]),
            page=page,
            page_size=page_size,
        )

    async def search_by_owner(
        self,
        owner_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """
        Search for assets owned by a specific user.

        Args:
            owner_id: Owner ID
            page: Page number
            page_size: Results per page

        Returns:
            SearchResponse with owned assets
        """
        return await self.search(
            query="",
            filters=SearchFilter(owner_ids=[owner_id]),
            page=page,
            page_size=page_size,
        )

    async def suggest(
        self,
        prefix: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Get search suggestions based on prefix.

        Args:
            prefix: Search prefix
            limit: Maximum suggestions

        Returns:
            List of suggested search terms
        """
        assets = await self.navigator.list_assets(limit=1000)
        suggestions = set()

        prefix_lower = prefix.lower()

        for asset in assets:
            if asset.name.lower().startswith(prefix_lower):
                suggestions.add(asset.name)

            if asset.description:
                words = asset.description.lower().split()
                for word in words:
                    if word.startswith(prefix_lower) and len(word) > 3:
                        suggestions.add(word)

        return sorted(suggestions)[:limit]

    def _apply_filters(
        self,
        assets: list[DataAsset],
        filters: SearchFilter,
    ) -> list[DataAsset]:
        """Apply filters to asset list."""
        result = assets

        if filters.asset_types:
            result = [a for a in result if a.asset_type in filters.asset_types]

        if filters.source_systems:
            result = [a for a in result if a.source_system in filters.source_systems]

        if filters.owner_ids:
            result = [
                a for a in result
                if a.owner and a.owner.id in filters.owner_ids
            ]

        if filters.tags:
            tag_set = set(filters.tags)
            result = [
                a for a in result
                if any(t.key in tag_set or t.value in tag_set for t in a.tags)
            ]

        if filters.classifications:
            result = [
                a for a in result
                if a.classification in filters.classifications
            ]

        if filters.created_after:
            result = [a for a in result if a.created_at >= filters.created_after]

        if filters.created_before:
            result = [a for a in result if a.created_at <= filters.created_before]

        if filters.updated_after:
            result = [a for a in result if a.updated_at >= filters.updated_after]

        if filters.updated_before:
            result = [a for a in result if a.updated_at <= filters.updated_before]

        return result

    def _calculate_relevance(
        self,
        asset: DataAsset,
        query_terms: list[str],
    ) -> tuple[float, dict[str, list[str]], list[str]]:
        """
        Calculate relevance score for an asset.

        Returns:
            Tuple of (score, highlights, matched_fields)
        """
        if not query_terms:
            return 1.0, {}, []  # No query = all match

        score = 0.0
        highlights: dict[str, list[str]] = {}
        matched_fields: list[str] = []

        # Check name (highest weight)
        name_lower = asset.name.lower()
        name_matches = sum(1 for term in query_terms if term in name_lower)
        if name_matches > 0:
            score += name_matches * 3.0
            matched_fields.append("name")
            highlights["name"] = [asset.name]

        # Check qualified name
        qname_lower = asset.qualified_name.lower()
        qname_matches = sum(1 for term in query_terms if term in qname_lower)
        if qname_matches > 0:
            score += qname_matches * 2.0
            matched_fields.append("qualified_name")

        # Check description
        if asset.description:
            desc_lower = asset.description.lower()
            desc_matches = sum(1 for term in query_terms if term in desc_lower)
            if desc_matches > 0:
                score += desc_matches * 1.5
                matched_fields.append("description")
                # Create highlight snippets
                highlights["description"] = self._create_highlights(
                    asset.description, query_terms
                )

        # Check column names
        if asset.schema_metadata:
            for col in asset.schema_metadata.columns:
                col_lower = col.name.lower()
                if any(term in col_lower for term in query_terms):
                    score += 1.0
                    if "columns" not in matched_fields:
                        matched_fields.append("columns")

        # Check tags
        for tag in asset.tags:
            tag_key_lower = tag.key.lower()
            tag_val_lower = (tag.value or "").lower()
            if any(term in tag_key_lower or term in tag_val_lower for term in query_terms):
                score += 0.5
                if "tags" not in matched_fields:
                    matched_fields.append("tags")

        # Normalize score to 0-1 range
        max_possible = len(query_terms) * 8  # Approximate max score
        normalized_score = min(1.0, score / max_possible) if max_possible > 0 else 0.0

        return normalized_score, highlights, matched_fields

    def _create_highlights(
        self,
        text: str,
        query_terms: list[str],
        context_chars: int = 50,
    ) -> list[str]:
        """Create highlighted snippets from text."""
        highlights = []
        text_lower = text.lower()

        for term in query_terms:
            idx = text_lower.find(term)
            if idx >= 0:
                start = max(0, idx - context_chars)
                end = min(len(text), idx + len(term) + context_chars)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                highlights.append(snippet)

        return highlights[:3]  # Limit to 3 highlights

    def _sort_results(
        self,
        results: list[SearchResult],
        sort_by: SortField,
        sort_order: SortOrder,
    ) -> list[SearchResult]:
        """Sort search results."""
        reverse = sort_order == SortOrder.DESC

        if sort_by == SortField.RELEVANCE:
            return sorted(results, key=lambda r: r.score, reverse=reverse)
        elif sort_by == SortField.NAME:
            return sorted(results, key=lambda r: r.asset.name, reverse=reverse)
        elif sort_by == SortField.UPDATED_AT:
            return sorted(results, key=lambda r: r.asset.updated_at, reverse=reverse)
        elif sort_by == SortField.CREATED_AT:
            return sorted(results, key=lambda r: r.asset.created_at, reverse=reverse)
        else:
            return results
