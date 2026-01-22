/**
 * Shared Hooks
 *
 * React Query hooks for data fetching across analytics components.
 */

export {
  useObjects,
  objectsQueryKeys,
  type UseObjectsOptions,
  type UseObjectsResult,
} from './useObjects';

export {
  useObject,
  objectQueryKeys,
  type UseObjectOptions,
  type UseObjectResult,
  type ObjectWithRelations,
} from './useObject';

export {
  useRelationships,
  relationshipsQueryKeys,
  type UseRelationshipsOptions,
  type UseRelationshipsResult,
} from './useRelationships';

export {
  useTimeline,
  timelineQueryKeys,
  type UseTimelineOptions,
  type UseTimelineResult,
} from './useTimeline';

export {
  useAggregations,
  aggregationsQueryKeys,
  type UseAggregationsOptions,
  type UseAggregationsResult,
  type AggregationsData,
  type AggregationsQueryParams,
} from './useAggregations';

export {
  useSearch,
  searchQueryKeys,
  type UseSearchOptions,
  type UseSearchResult,
  type SearchQueryParams,
} from './useSearch';
