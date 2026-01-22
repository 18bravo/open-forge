/**
 * Editor Component
 *
 * Main editor component for Forge Studio. Provides the primary interface
 * for building and editing studio applications.
 */

import React from 'react';
import type {
  StudioApp,
  StudioPage,
  WidgetInstance,
  EditorState,
} from '../../types';

// ============================================================================
// Props Interfaces
// ============================================================================

export interface EditorProps {
  /** Initial app to load */
  app?: StudioApp;

  /** Callback when app changes */
  onAppChange?: (app: StudioApp) => void;

  /** Callback when save is requested */
  onSave?: (app: StudioApp) => Promise<void>;

  /** Callback when publish is requested */
  onPublish?: (app: StudioApp) => Promise<void>;

  /** Read-only mode */
  readOnly?: boolean;

  /** Custom class name */
  className?: string;
}

export interface EditorContextValue {
  /** Current editor state */
  state: EditorState;

  /** Select a page */
  selectPage: (pageId: string) => void;

  /** Select a widget */
  selectWidget: (widgetId: string | null) => void;

  /** Add a new page */
  addPage: (page: Partial<StudioPage>) => void;

  /** Update a page */
  updatePage: (pageId: string, updates: Partial<StudioPage>) => void;

  /** Delete a page */
  deletePage: (pageId: string) => void;

  /** Add a widget to current page */
  addWidget: (widget: WidgetInstance) => void;

  /** Update a widget */
  updateWidget: (widgetId: string, updates: Partial<WidgetInstance>) => void;

  /** Delete a widget */
  deleteWidget: (widgetId: string) => void;

  /** Undo last action */
  undo: () => void;

  /** Redo last undone action */
  redo: () => void;

  /** Check if undo is available */
  canUndo: boolean;

  /** Check if redo is available */
  canRedo: boolean;

  /** Toggle preview mode */
  togglePreview: () => void;

  /** Set active panel */
  setActivePanel: (panel: EditorState['activePanel']) => void;

  /** Set zoom level */
  setZoom: (zoom: number) => void;
}

// ============================================================================
// Context
// ============================================================================

export const EditorContext = React.createContext<EditorContextValue | null>(null);

/**
 * Hook to access editor context
 */
export function useEditor(): EditorContextValue {
  const context = React.useContext(EditorContext);
  if (!context) {
    throw new Error('useEditor must be used within an EditorProvider');
  }
  return context;
}

// ============================================================================
// Component
// ============================================================================

/**
 * Main Editor component for Forge Studio
 *
 * @example
 * ```tsx
 * <Editor
 *   app={myApp}
 *   onAppChange={handleAppChange}
 *   onSave={handleSave}
 * />
 * ```
 */
export const Editor: React.FC<EditorProps> = ({
  app: _app,
  onAppChange: _onAppChange,
  onSave: _onSave,
  onPublish: _onPublish,
  readOnly: _readOnly = false,
  className: _className,
}) => {
  // TODO: Implement editor state management
  // TODO: Implement undo/redo
  // TODO: Implement keyboard shortcuts
  // TODO: Implement drag-and-drop

  return (
    <div data-testid="forge-studio-editor">
      {/* TODO: Implement editor layout */}
      {/* - Toolbar */}
      {/* - Sidebar (WidgetPanel) */}
      {/* - Canvas */}
      {/* - ConfigPanel */}
      {/* - CodeEditor (modal/drawer) */}
    </div>
  );
};

Editor.displayName = 'Editor';

export default Editor;
