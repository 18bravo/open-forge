/**
 * Defense Enterprise 3D - Type Definitions
 */

// Geographic Combatant Command
export interface CombatantCommand {
  id: string;
  name: string;
  abbrev: string;
  type: 'geographic' | 'functional';
  lat?: number;
  lon?: number;
  hq: string;
  color: string;
  mission: string;
  aor?: string; // Area of Responsibility
  established: number;
  commander?: string;
  components: string[];
  keyFacts: string[];
}

// Organization Node
export interface OrgNode {
  id: string;
  name: string;
  abbrev: string;
  type: 'department' | 'component' | 'command' | 'agency';
  position: [number, number, number];
  size: number;
  color: string;
  level: number;
  parentId?: string;
  description: string;
  responsibilities: string[];
  budget?: string;
  personnel?: string;
}

// Strategic Document
export interface StrategicDocument {
  id: string;
  name: string;
  abbrev: string;
  level: number;
  source: string;
  color: string;
  description: string;
  keyThemes: string[];
  updateCycle: string;
  currentVersion?: string;
  relationship: string;
}

// PPBE Phase
export interface PPBEPhase {
  id: string;
  name: string;
  abbrev: string;
  color: string;
  duration: string;
  description: string;
  keyActivities: string[];
  outputs: string[];
  stakeholders: string[];
}

// Learning Module
export interface LearningModule {
  id: string;
  title: string;
  description: string;
  duration: string;
  topics: string[];
  quiz?: QuizQuestion[];
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

// View Types
export type ViewId = 'globe' | 'organization' | 'ppbe' | 'strategy' | 'learn';

export interface ViewConfig {
  id: ViewId;
  label: string;
  icon: string;
  description: string;
}

// Selection State
export interface SelectionState {
  type: 'ccmd' | 'org' | 'strategy' | 'ppbe' | null;
  id: string | null;
  data: CombatantCommand | OrgNode | StrategicDocument | PPBEPhase | null;
}

// Search Result
export interface SearchResult {
  type: 'ccmd' | 'org' | 'strategy' | 'ppbe';
  id: string;
  name: string;
  abbrev: string;
  description: string;
}
