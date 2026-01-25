'use client';

/**
 * Defense Enterprise 3D - Interactive Learning Platform
 *
 * A visually stunning yet functionally useful educational tool for understanding
 * the Department of Defense enterprise, including:
 * - Combatant Commands (geographic & functional)
 * - DoD organizational structure
 * - PPBE resource allocation process
 * - Strategic guidance cascade
 * - Interactive learning modules with quizzes
 */

import { Suspense } from 'react';
import { useDefenseEnterprise } from './hooks';
import { Navigation, InfoPanel } from './components';
import { GlobeView, OrganizationView, PPBEView, StrategyView, LearnView } from './views';

// Loading fallback for 3D views
function ViewLoading() {
  return (
    <div className="w-full h-full flex items-center justify-center bg-slate-900">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-400 text-sm">Loading visualization...</p>
      </div>
    </div>
  );
}

export function DefenseEnterprise3D() {
  const {
    currentView,
    setCurrentView,
    selection,
    selectCommand,
    selectOrgNode,
    selectStrategy,
    selectPPBE,
    clearSelection,
    searchQuery,
    setSearchQuery,
    searchResults,
    selectSearchResult,
    showFunctionalCommands,
    showGeographicCommands,
  } = useDefenseEnterprise();

  return (
    <div className="relative w-full h-screen bg-slate-900 overflow-hidden">
      {/* Navigation */}
      <Navigation
        currentView={currentView}
        onViewChange={setCurrentView}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchResults={searchResults}
        onResultSelect={selectSearchResult}
      />

      {/* Main Content Area */}
      <div className="absolute inset-0 pt-28">
        <Suspense fallback={<ViewLoading />}>
          {currentView === 'globe' && (
            <GlobeView
              selectedId={selection.type === 'ccmd' ? selection.id : null}
              onSelect={selectCommand}
              showGeographic={showGeographicCommands}
              showFunctional={showFunctionalCommands}
            />
          )}
          {currentView === 'organization' && (
            <OrganizationView
              selectedId={selection.type === 'org' ? selection.id : null}
              onSelect={selectOrgNode}
            />
          )}
          {currentView === 'ppbe' && (
            <PPBEView
              selectedId={selection.type === 'ppbe' ? selection.id : null}
              onSelect={selectPPBE}
            />
          )}
          {currentView === 'strategy' && (
            <StrategyView
              selectedId={selection.type === 'strategy' ? selection.id : null}
              onSelect={selectStrategy}
            />
          )}
          {currentView === 'learn' && (
            <LearnView />
          )}
        </Suspense>
      </div>

      {/* Info Panel */}
      {selection.data && currentView !== 'learn' && (
        <InfoPanel selection={selection} onClose={clearSelection} />
      )}

      {/* View-specific controls */}
      {currentView === 'globe' && (
        <GlobeControls
          showGeographic={showGeographicCommands}
          showFunctional={showFunctionalCommands}
        />
      )}
    </div>
  );
}

interface GlobeControlsProps {
  showGeographic: boolean;
  showFunctional: boolean;
}

function GlobeControls({ showGeographic, showFunctional }: GlobeControlsProps) {
  return (
    <div className="absolute top-32 right-6 bg-slate-900/90 backdrop-blur-xl rounded-lg border border-slate-700/50 p-4 z-30">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        View Controls
      </h3>
      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showGeographic}
            onChange={() => {}}
            className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500/50"
          />
          <span className="text-sm text-slate-300">Geographic (6)</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showFunctional}
            onChange={() => {}}
            className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-purple-500 focus:ring-purple-500/50"
          />
          <span className="text-sm text-slate-300">Functional (5)</span>
        </label>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <p className="text-xs text-slate-500">
          Click markers for details
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Drag to rotate, scroll to zoom
        </p>
      </div>
    </div>
  );
}

// Default export for easier importing
export default DefenseEnterprise3D;
