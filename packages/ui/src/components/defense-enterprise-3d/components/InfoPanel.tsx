'use client';

/**
 * Information Panel - Displays detailed information about selected items
 */

import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Building2, FileText, Clock, Users, DollarSign, Target, ChevronRight } from 'lucide-react';
import type { SelectionState, CombatantCommand, OrgNode, StrategicDocument, PPBEPhase } from '../types';

interface InfoPanelProps {
  selection: SelectionState;
  onClose: () => void;
}

export function InfoPanel({ selection, onClose }: InfoPanelProps) {
  if (!selection.data) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="absolute right-0 top-0 h-full w-96 bg-slate-900/95 backdrop-blur-xl border-l border-slate-700/50 overflow-hidden z-50"
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div
            className="p-6 border-b border-slate-700/50"
            style={{
              background: `linear-gradient(135deg, ${getColor(selection)}20, transparent)`
            }}
          >
            <div className="flex items-start justify-between">
              <div>
                <span
                  className="inline-block px-2 py-0.5 rounded text-xs font-medium mb-2"
                  style={{ backgroundColor: `${getColor(selection)}30`, color: getColor(selection) }}
                >
                  {getTypeLabel(selection.type)}
                </span>
                <h2 className="text-xl font-bold text-white">
                  {getTitle(selection.data)}
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  {getAbbrev(selection.data)}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {selection.type === 'ccmd' && (
              <CommandDetails command={selection.data as CombatantCommand} />
            )}
            {selection.type === 'org' && (
              <OrgDetails node={selection.data as OrgNode} />
            )}
            {selection.type === 'strategy' && (
              <StrategyDetails doc={selection.data as StrategicDocument} />
            )}
            {selection.type === 'ppbe' && (
              <PPBEDetails phase={selection.data as PPBEPhase} />
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function CommandDetails({ command }: { command: CombatantCommand }) {
  return (
    <>
      {/* Mission */}
      <Section title="Mission">
        <p className="text-slate-300 text-sm leading-relaxed">{command.mission}</p>
      </Section>

      {/* Quick Facts */}
      <Section title="Quick Facts">
        <div className="grid grid-cols-2 gap-3">
          <FactCard icon={MapPin} label="Headquarters" value={command.hq} />
          <FactCard icon={Clock} label="Established" value={command.established.toString()} />
          {command.aor && (
            <div className="col-span-2">
              <FactCard icon={Target} label="AOR" value={command.aor} />
            </div>
          )}
        </div>
      </Section>

      {/* Components */}
      <Section title="Service Components">
        <div className="flex flex-wrap gap-2">
          {command.components.map(comp => (
            <span
              key={comp}
              className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300 font-mono"
            >
              {comp}
            </span>
          ))}
        </div>
      </Section>

      {/* Key Facts */}
      <Section title="Key Facts">
        <ul className="space-y-2">
          {command.keyFacts.map((fact, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <ChevronRight className="w-4 h-4 mt-0.5 text-slate-500 flex-shrink-0" />
              <span>{fact}</span>
            </li>
          ))}
        </ul>
      </Section>
    </>
  );
}

function OrgDetails({ node }: { node: OrgNode }) {
  return (
    <>
      {/* Description */}
      <Section title="Description">
        <p className="text-slate-300 text-sm leading-relaxed">{node.description}</p>
      </Section>

      {/* Quick Facts */}
      {(node.budget || node.personnel) && (
        <Section title="Quick Facts">
          <div className="space-y-3">
            {node.budget && (
              <FactCard icon={DollarSign} label="Budget" value={node.budget} />
            )}
            {node.personnel && (
              <FactCard icon={Users} label="Personnel" value={node.personnel} />
            )}
          </div>
        </Section>
      )}

      {/* Responsibilities */}
      <Section title="Key Responsibilities">
        <ul className="space-y-2">
          {node.responsibilities.map((resp, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <ChevronRight className="w-4 h-4 mt-0.5 text-slate-500 flex-shrink-0" />
              <span>{resp}</span>
            </li>
          ))}
        </ul>
      </Section>
    </>
  );
}

function StrategyDetails({ doc }: { doc: StrategicDocument }) {
  return (
    <>
      {/* Description */}
      <Section title="Purpose">
        <p className="text-slate-300 text-sm leading-relaxed">{doc.description}</p>
      </Section>

      {/* Quick Facts */}
      <Section title="Document Info">
        <div className="space-y-3">
          <FactCard icon={Building2} label="Source" value={doc.source} />
          <FactCard icon={Clock} label="Update Cycle" value={doc.updateCycle} />
          {doc.currentVersion && (
            <FactCard icon={FileText} label="Current Version" value={doc.currentVersion} />
          )}
        </div>
      </Section>

      {/* Key Themes */}
      <Section title="Key Themes">
        <ul className="space-y-2">
          {doc.keyThemes.map((theme, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <ChevronRight className="w-4 h-4 mt-0.5 text-slate-500 flex-shrink-0" />
              <span>{theme}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Relationship */}
      <Section title="Strategic Relationship">
        <p className="text-slate-300 text-sm leading-relaxed">{doc.relationship}</p>
      </Section>
    </>
  );
}

function PPBEDetails({ phase }: { phase: PPBEPhase }) {
  return (
    <>
      {/* Description */}
      <Section title="Overview">
        <p className="text-slate-300 text-sm leading-relaxed">{phase.description}</p>
      </Section>

      {/* Timeline */}
      <Section title="Duration">
        <FactCard icon={Clock} label="Timeframe" value={phase.duration} />
      </Section>

      {/* Key Activities */}
      <Section title="Key Activities">
        <ul className="space-y-2">
          {phase.keyActivities.map((activity, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
              <ChevronRight className="w-4 h-4 mt-0.5 text-slate-500 flex-shrink-0" />
              <span>{activity}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Outputs */}
      <Section title="Key Outputs">
        <div className="flex flex-wrap gap-2">
          {phase.outputs.map((output, i) => (
            <span
              key={i}
              className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300"
            >
              {output}
            </span>
          ))}
        </div>
      </Section>

      {/* Stakeholders */}
      <Section title="Key Stakeholders">
        <div className="flex flex-wrap gap-2">
          {phase.stakeholders.map((stakeholder, i) => (
            <span
              key={i}
              className="px-2 py-1 bg-slate-800/50 border border-slate-700 rounded text-xs text-slate-400"
            >
              {stakeholder}
            </span>
          ))}
        </div>
      </Section>
    </>
  );
}

// Helper Components
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

interface FactCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}

function FactCard({ icon: Icon, label, value }: FactCardProps) {
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg">
      <Icon className="w-4 h-4 text-slate-500 mt-0.5" />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm text-slate-300">{value}</p>
      </div>
    </div>
  );
}

// Helper functions
function getColor(selection: SelectionState): string {
  if (!selection.data) return '#3b82f6';
  if ('color' in selection.data) return selection.data.color;
  return '#3b82f6';
}

function getTypeLabel(type: SelectionState['type']): string {
  switch (type) {
    case 'ccmd': return 'Combatant Command';
    case 'org': return 'Organization';
    case 'strategy': return 'Strategic Document';
    case 'ppbe': return 'PPBE Phase';
    default: return '';
  }
}

function getTitle(data: SelectionState['data']): string {
  if (!data) return '';
  return data.name;
}

function getAbbrev(data: SelectionState['data']): string {
  if (!data) return '';
  return data.abbrev;
}
