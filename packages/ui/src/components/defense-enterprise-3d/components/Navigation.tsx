'use client';

/**
 * Navigation - View switching and search
 */

import { motion } from 'framer-motion';
import { Globe2, Network, GitBranch, FileStack, GraduationCap, Search, X } from 'lucide-react';
import type { ViewId, SearchResult } from '../types';

interface NavigationProps {
  currentView: ViewId;
  onViewChange: (view: ViewId) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  searchResults: SearchResult[];
  onResultSelect: (result: SearchResult) => void;
}

const VIEWS = [
  { id: 'globe' as ViewId, label: 'Globe', icon: Globe2, description: 'Geographic & Functional Commands' },
  { id: 'organization' as ViewId, label: 'Organization', icon: Network, description: 'DoD Structure' },
  { id: 'ppbe' as ViewId, label: 'PPBE', icon: GitBranch, description: 'Resource Process' },
  { id: 'strategy' as ViewId, label: 'Strategy', icon: FileStack, description: 'Guidance Cascade' },
  { id: 'learn' as ViewId, label: 'Learn', icon: GraduationCap, description: 'Interactive Modules' },
];

export function Navigation({
  currentView,
  onViewChange,
  searchQuery,
  onSearchChange,
  searchResults,
  onResultSelect
}: NavigationProps) {
  return (
    <div className="absolute top-0 left-0 right-0 z-40">
      {/* Top Bar */}
      <div className="bg-slate-900/90 backdrop-blur-xl border-b border-slate-700/50">
        <div className="flex items-center justify-between px-6 py-3">
          {/* Logo/Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Globe2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Defense Enterprise</h1>
              <p className="text-xs text-slate-400">Interactive Learning Platform</p>
            </div>
          </div>

          {/* Search */}
          <div className="relative w-80">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search commands, organizations, documents..."
                className="w-full pl-10 pr-10 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
              />
              {searchQuery && (
                <button
                  onClick={() => onSearchChange('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 hover:bg-slate-700 rounded"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              )}
            </div>

            {/* Search Results Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
                {searchResults.slice(0, 8).map((result) => (
                  <button
                    key={`${result.type}-${result.id}`}
                    onClick={() => onResultSelect(result)}
                    className="w-full px-4 py-3 flex items-start gap-3 hover:bg-slate-700/50 transition-colors text-left"
                  >
                    <span className={`
                      px-1.5 py-0.5 rounded text-xs font-medium
                      ${result.type === 'ccmd' ? 'bg-blue-500/20 text-blue-400' : ''}
                      ${result.type === 'org' ? 'bg-purple-500/20 text-purple-400' : ''}
                      ${result.type === 'strategy' ? 'bg-amber-500/20 text-amber-400' : ''}
                      ${result.type === 'ppbe' ? 'bg-green-500/20 text-green-400' : ''}
                    `}>
                      {result.abbrev}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{result.name}</p>
                      <p className="text-xs text-slate-400 truncate">{result.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="flex items-center gap-6 text-sm">
            <div className="text-center">
              <p className="text-white font-semibold">11</p>
              <p className="text-slate-500 text-xs">Commands</p>
            </div>
            <div className="text-center">
              <p className="text-white font-semibold">$886B</p>
              <p className="text-slate-500 text-xs">FY2024 Budget</p>
            </div>
            <div className="text-center">
              <p className="text-white font-semibold">2.9M</p>
              <p className="text-slate-500 text-xs">Personnel</p>
            </div>
          </div>
        </div>

        {/* View Tabs */}
        <div className="flex items-center gap-1 px-6 pb-3">
          {VIEWS.map((view) => {
            const isActive = currentView === view.id;
            return (
              <button
                key={view.id}
                onClick={() => onViewChange(view.id)}
                className={`
                  relative px-4 py-2 rounded-lg flex items-center gap-2 transition-all
                  ${isActive
                    ? 'text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }
                `}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-slate-800 rounded-lg"
                    transition={{ type: 'spring', duration: 0.3 }}
                  />
                )}
                <view.icon className="w-4 h-4 relative z-10" />
                <span className="text-sm font-medium relative z-10">{view.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
