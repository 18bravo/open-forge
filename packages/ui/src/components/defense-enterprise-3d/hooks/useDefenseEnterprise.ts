/**
 * Main state management hook for Defense Enterprise 3D
 */

import { useState, useCallback, useMemo } from 'react';
import type { ViewId, SelectionState, SearchResult } from '../types';
import { ALL_COMMANDS } from '../data/combatant-commands';
import { ORG_NODES } from '../data/organization';
import { STRATEGIC_DOCUMENTS } from '../data/strategy';
import { PPBE_PHASES } from '../data/ppbe';

export function useDefenseEnterprise() {
  const [currentView, setCurrentView] = useState<ViewId>('globe');
  const [selection, setSelection] = useState<SelectionState>({
    type: null,
    id: null,
    data: null
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFunctionalCommands, setShowFunctionalCommands] = useState(true);
  const [showGeographicCommands, setShowGeographicCommands] = useState(true);
  const [animationSpeed, setAnimationSpeed] = useState(1);

  // Clear selection when changing views
  const handleViewChange = useCallback((view: ViewId) => {
    setCurrentView(view);
    setSelection({ type: null, id: null, data: null });
  }, []);

  // Select a combatant command
  const selectCommand = useCallback((id: string) => {
    const command = ALL_COMMANDS.find(c => c.id === id);
    if (command) {
      setSelection({ type: 'ccmd', id, data: command });
    }
  }, []);

  // Select an organization node
  const selectOrgNode = useCallback((id: string) => {
    const node = ORG_NODES.find(n => n.id === id);
    if (node) {
      setSelection({ type: 'org', id, data: node });
    }
  }, []);

  // Select a strategic document
  const selectStrategy = useCallback((id: string) => {
    const doc = STRATEGIC_DOCUMENTS.find(d => d.id === id);
    if (doc) {
      setSelection({ type: 'strategy', id, data: doc });
    }
  }, []);

  // Select a PPBE phase
  const selectPPBE = useCallback((id: string) => {
    const phase = PPBE_PHASES.find(p => p.id === id);
    if (phase) {
      setSelection({ type: 'ppbe', id, data: phase });
    }
  }, []);

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelection({ type: null, id: null, data: null });
  }, []);

  // Search across all data
  const searchResults = useMemo((): SearchResult[] => {
    if (!searchQuery.trim()) return [];

    const query = searchQuery.toLowerCase();
    const results: SearchResult[] = [];

    // Search commands
    ALL_COMMANDS.forEach(cmd => {
      if (
        cmd.name.toLowerCase().includes(query) ||
        cmd.abbrev.toLowerCase().includes(query) ||
        cmd.mission.toLowerCase().includes(query)
      ) {
        results.push({
          type: 'ccmd',
          id: cmd.id,
          name: cmd.name,
          abbrev: cmd.abbrev,
          description: cmd.mission
        });
      }
    });

    // Search org nodes
    ORG_NODES.forEach(node => {
      if (
        node.name.toLowerCase().includes(query) ||
        node.abbrev.toLowerCase().includes(query) ||
        node.description.toLowerCase().includes(query)
      ) {
        results.push({
          type: 'org',
          id: node.id,
          name: node.name,
          abbrev: node.abbrev,
          description: node.description
        });
      }
    });

    // Search strategy docs
    STRATEGIC_DOCUMENTS.forEach(doc => {
      if (
        doc.name.toLowerCase().includes(query) ||
        doc.abbrev.toLowerCase().includes(query) ||
        doc.description.toLowerCase().includes(query)
      ) {
        results.push({
          type: 'strategy',
          id: doc.id,
          name: doc.name,
          abbrev: doc.abbrev,
          description: doc.description
        });
      }
    });

    // Search PPBE phases
    PPBE_PHASES.forEach(phase => {
      if (
        phase.name.toLowerCase().includes(query) ||
        phase.description.toLowerCase().includes(query)
      ) {
        results.push({
          type: 'ppbe',
          id: phase.id,
          name: phase.name,
          abbrev: phase.abbrev,
          description: phase.description
        });
      }
    });

    return results;
  }, [searchQuery]);

  // Handle search result selection
  const selectSearchResult = useCallback((result: SearchResult) => {
    switch (result.type) {
      case 'ccmd':
        setCurrentView('globe');
        selectCommand(result.id);
        break;
      case 'org':
        setCurrentView('organization');
        selectOrgNode(result.id);
        break;
      case 'strategy':
        setCurrentView('strategy');
        selectStrategy(result.id);
        break;
      case 'ppbe':
        setCurrentView('ppbe');
        selectPPBE(result.id);
        break;
    }
    setSearchQuery('');
  }, [selectCommand, selectOrgNode, selectStrategy, selectPPBE]);

  return {
    // View state
    currentView,
    setCurrentView: handleViewChange,

    // Selection state
    selection,
    selectCommand,
    selectOrgNode,
    selectStrategy,
    selectPPBE,
    clearSelection,

    // Search
    searchQuery,
    setSearchQuery,
    searchResults,
    selectSearchResult,

    // Filters
    showFunctionalCommands,
    setShowFunctionalCommands,
    showGeographicCommands,
    setShowGeographicCommands,

    // Animation
    animationSpeed,
    setAnimationSpeed
  };
}

export type DefenseEnterpriseState = ReturnType<typeof useDefenseEnterprise>;
