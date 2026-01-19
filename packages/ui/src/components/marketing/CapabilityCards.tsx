'use client';

import { Suspense } from 'react';
import { CanvasWrapper, OntologyAnimation, AgentSwarmAnimation, CodeLoopAnimation, TimelineAnimation } from './three';

interface CapabilityCardProps {
  title: string;
  description: string;
  animation: 'ontology' | 'swarm' | 'codeloop' | 'timeline';
}

function CapabilityCard({ title, description, animation }: CapabilityCardProps) {
  const AnimationComponent = {
    ontology: OntologyAnimation,
    swarm: AgentSwarmAnimation,
    codeloop: CodeLoopAnimation,
    timeline: TimelineAnimation,
  }[animation];

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50 hover:bg-zinc-900">
      {/* Three.js Background */}
      <div className="absolute inset-0 opacity-30 group-hover:opacity-50 transition-opacity">
        <Suspense fallback={null}>
          <CanvasWrapper className="h-full w-full">
            <AnimationComponent />
          </CanvasWrapper>
        </Suspense>
      </div>

      {/* Content */}
      <div className="relative z-10">
        <h3 className="mb-3 text-xl font-semibold text-zinc-50">{title}</h3>
        <p className="text-sm text-zinc-400 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}

const capabilities: CapabilityCardProps[] = [
  {
    title: 'The Ontology Engine',
    description:
      'Define the semantic, kinetic, and dynamic elements of your business—objects, actions, relationships—in an open schema language. Your ontology compiles to SQL, GraphQL, Pydantic, TypeScript, and Cypher. No proprietary formats. No lock-in.',
    animation: 'ontology',
  },
  {
    title: 'Autonomous Agent Clusters',
    description:
      'Six specialized clusters—Discovery, Data Architect, App Builder, Operations, Enablement, and Orchestration—coordinate to analyze, design, build, and operate your data infrastructure. 20+ agents working in parallel, 24/7.',
    animation: 'swarm',
  },
  {
    title: 'Closed-Loop Code Generation',
    description:
      'From ontology to production in one workflow. Generate FastAPI routes, SQLAlchemy models, React components, test suites, and infrastructure configs. Agents validate, refine, and deploy—no consultants in the loop.',
    animation: 'codeloop',
  },
  {
    title: 'Day 1 Value',
    description:
      'Deploy on your infrastructure today. Connect your data sources. Watch agents discover schemas, design transformations, and generate working applications. Days, not years.',
    animation: 'timeline',
  },
];

export function CapabilityCards() {
  return (
    <section className="relative py-24" id="features">
      <div className="mx-auto max-w-6xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            Ontology-Powered.{' '}
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Agent-Operated.
            </span>
          </h2>
          <p className="text-xl text-zinc-400">
            Everything they promised. Nothing they control.
          </p>
        </div>

        {/* Cards grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {capabilities.map((capability) => (
            <CapabilityCard key={capability.title} {...capability} />
          ))}
        </div>
      </div>
    </section>
  );
}
