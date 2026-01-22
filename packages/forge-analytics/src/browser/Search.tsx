/**
 * Search Component
 *
 * Full-text search across objects with fuzzy matching,
 * suggestions, recent searches, and highlighted results.
 */

import React from 'react';
import type {
  BaseAnalyticsProps,
  SearchConfig,
  SearchResult,
  SearchHighlight,
  ObjectTypeRef,
} from '../types';

// ============================================================================
// Component Props
// ============================================================================

export interface SearchProps extends BaseAnalyticsProps {
  /** Search configuration */
  config: SearchConfig;

  /** Current search query */
  query?: string;

  /** Search results */
  results?: SearchResult[];

  /** Recent searches */
  recentSearches?: string[];

  /** Search suggestions */
  suggestions?: SearchSuggestion[];

  /** Whether search is in progress */
  isSearching?: boolean;

  /** Query change handler */
  onQueryChange?: (query: string) => void;

  /** Search submit handler */
  onSearch?: (query: string) => void;

  /** Result click handler */
  onResultClick?: (result: SearchResult) => void;

  /** Recent search click handler */
  onRecentSearchClick?: (query: string) => void;

  /** Clear recent searches handler */
  onClearRecentSearches?: () => void;

  /** Suggestion click handler */
  onSuggestionClick?: (suggestion: SearchSuggestion) => void;

  /** Clear handler */
  onClear?: () => void;
}

// ============================================================================
// Data Types
// ============================================================================

/**
 * Search suggestion item
 */
export interface SearchSuggestion {
  /** Suggestion type */
  type: 'query' | 'object' | 'property' | 'filter';

  /** Display text */
  text: string;

  /** Description */
  description?: string;

  /** Associated object type (for object suggestions) */
  objectType?: ObjectTypeRef;

  /** Associated object ID (for object suggestions) */
  objectId?: string;

  /** Filter to apply (for filter suggestions) */
  filter?: { property: string; operator: string; value: unknown };
}

// ============================================================================
// Sub-component Props
// ============================================================================

export interface SearchInputProps {
  /** Current value */
  value: string;

  /** Placeholder text */
  placeholder?: string;

  /** Whether search is in progress */
  isSearching?: boolean;

  /** Auto-focus on mount */
  autoFocus?: boolean;

  /** Minimum characters before search */
  minCharacters?: number;

  /** Value change handler */
  onChange?: (value: string) => void;

  /** Submit handler */
  onSubmit?: () => void;

  /** Clear handler */
  onClear?: () => void;

  /** Focus handler */
  onFocus?: () => void;

  /** Blur handler */
  onBlur?: () => void;

  /** Keyboard navigation handlers */
  onKeyDown?: (event: React.KeyboardEvent) => void;
}

export interface SearchResultsListProps {
  /** Search results */
  results: SearchResult[];

  /** Currently highlighted index (for keyboard nav) */
  highlightedIndex?: number;

  /** Maximum results to show */
  maxResults?: number;

  /** Result click handler */
  onResultClick?: (result: SearchResult) => void;

  /** Result hover handler */
  onResultHover?: (index: number) => void;

  /** Empty results message */
  emptyMessage?: string;
}

export interface SearchResultItemProps {
  /** Search result */
  result: SearchResult;

  /** Whether item is highlighted */
  highlighted?: boolean;

  /** Click handler */
  onClick?: () => void;

  /** Hover handler */
  onHover?: () => void;
}

export interface RecentSearchesListProps {
  /** Recent searches */
  searches: string[];

  /** Maximum items to show */
  maxItems?: number;

  /** Search click handler */
  onSearchClick?: (query: string) => void;

  /** Clear all handler */
  onClearAll?: () => void;

  /** Remove single search handler */
  onRemove?: (query: string) => void;
}

export interface SuggestionsListProps {
  /** Suggestions */
  suggestions: SearchSuggestion[];

  /** Currently highlighted index */
  highlightedIndex?: number;

  /** Suggestion click handler */
  onSuggestionClick?: (suggestion: SearchSuggestion) => void;

  /** Suggestion hover handler */
  onSuggestionHover?: (index: number) => void;
}

export interface HighlightedTextProps {
  /** Original text */
  text: string;

  /** Highlight matches */
  highlights?: SearchHighlight['matches'];

  /** Highlight CSS class */
  highlightClassName?: string;
}

// ============================================================================
// Component
// ============================================================================

/**
 * Search component for finding objects
 */
export const Search: React.FC<SearchProps> = ({
  config: _config,
  query: _query,
  results: _results,
  recentSearches: _recentSearches,
  suggestions: _suggestions,
  isSearching: _isSearching = false,
  onQueryChange: _onQueryChange,
  onSearch: _onSearch,
  onResultClick: _onResultClick,
  onRecentSearchClick: _onRecentSearchClick,
  onClearRecentSearches: _onClearRecentSearches,
  onSuggestionClick: _onSuggestionClick,
  onClear: _onClear,
  className: _className,
  style: _style,
  isLoading: _isLoading = false,
  error: _error,
  disabled: _disabled = false,
}) => {
  // TODO: Implement search input with debouncing
  // TODO: Implement results dropdown
  // TODO: Implement suggestions dropdown
  // TODO: Implement recent searches dropdown
  // TODO: Implement keyboard navigation
  // TODO: Implement fuzzy matching
  // TODO: Implement result highlighting
  // TODO: Implement loading state
  // TODO: Implement error state
  // TODO: Implement empty state

  return (
    <div data-testid="analytics-search">
      {/* TODO: Implement Search */}
    </div>
  );
};

Search.displayName = 'Search';

// ============================================================================
// Sub-components (Stubs)
// ============================================================================

/**
 * Search input field with icon and clear button
 */
export const SearchInput: React.FC<SearchInputProps> = ({
  value: _value,
  placeholder: _placeholder = 'Search...',
  isSearching: _isSearching = false,
  autoFocus: _autoFocus = false,
  minCharacters: _minCharacters = 2,
  onChange: _onChange,
  onSubmit: _onSubmit,
  onClear: _onClear,
  onFocus: _onFocus,
  onBlur: _onBlur,
  onKeyDown: _onKeyDown,
}) => {
  // TODO: Implement input with search icon
  // TODO: Implement clear button
  // TODO: Implement loading spinner
  // TODO: Implement minimum character warning

  return (
    <div data-testid="search-input">
      {/* TODO: Implement search input */}
    </div>
  );
};

SearchInput.displayName = 'SearchInput';

/**
 * List of search results
 */
export const SearchResultsList: React.FC<SearchResultsListProps> = ({
  results: _results,
  highlightedIndex: _highlightedIndex,
  maxResults: _maxResults = 10,
  onResultClick: _onResultClick,
  onResultHover: _onResultHover,
  emptyMessage: _emptyMessage = 'No results found',
}) => {
  // TODO: Implement results list
  // TODO: Implement keyboard navigation highlighting
  // TODO: Implement "show more" for truncated results
  // TODO: Implement empty state

  return (
    <div data-testid="search-results-list">
      {/* TODO: Implement results list */}
    </div>
  );
};

SearchResultsList.displayName = 'SearchResultsList';

/**
 * Individual search result item
 */
export const SearchResultItem: React.FC<SearchResultItemProps> = ({
  result: _result,
  highlighted: _highlighted = false,
  onClick: _onClick,
  onHover: _onHover,
}) => {
  // TODO: Implement result item with title, subtitle
  // TODO: Implement object type badge
  // TODO: Implement highlighted text
  // TODO: Implement hover/selected styling

  return (
    <div data-testid="search-result-item">
      {/* TODO: Implement result item */}
    </div>
  );
};

SearchResultItem.displayName = 'SearchResultItem';

/**
 * List of recent searches
 */
export const RecentSearchesList: React.FC<RecentSearchesListProps> = ({
  searches: _searches,
  maxItems: _maxItems = 5,
  onSearchClick: _onSearchClick,
  onClearAll: _onClearAll,
  onRemove: _onRemove,
}) => {
  // TODO: Implement recent searches list
  // TODO: Implement clear all button
  // TODO: Implement individual remove buttons
  // TODO: Implement clock icon

  return (
    <div data-testid="recent-searches-list">
      {/* TODO: Implement recent searches */}
    </div>
  );
};

RecentSearchesList.displayName = 'RecentSearchesList';

/**
 * List of search suggestions
 */
export const SuggestionsList: React.FC<SuggestionsListProps> = ({
  suggestions: _suggestions,
  highlightedIndex: _highlightedIndex,
  onSuggestionClick: _onSuggestionClick,
  onSuggestionHover: _onSuggestionHover,
}) => {
  // TODO: Implement suggestions list grouped by type
  // TODO: Implement keyboard navigation
  // TODO: Implement suggestion icons by type

  return (
    <div data-testid="suggestions-list">
      {/* TODO: Implement suggestions */}
    </div>
  );
};

SuggestionsList.displayName = 'SuggestionsList';

/**
 * Text with highlighted search matches
 */
export const HighlightedText: React.FC<HighlightedTextProps> = ({
  text: _text,
  highlights: _highlights,
  highlightClassName: _highlightClassName = 'bg-yellow-200',
}) => {
  // TODO: Implement text splitting at highlight positions
  // TODO: Implement highlight styling

  return (
    <span data-testid="highlighted-text">
      {/* TODO: Implement highlighted text */}
    </span>
  );
};

HighlightedText.displayName = 'HighlightedText';

export default Search;
