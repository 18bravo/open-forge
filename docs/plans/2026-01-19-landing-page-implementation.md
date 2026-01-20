# Landing Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build forge.overlordai.ai landing page positioned as the open-source Palantir alternative with Three.js animations

**Architecture:** Next.js App Router with route group `(marketing)` for landing pages. Static content with client-side Three.js animations using react-three-fiber. Tailwind CSS with violet/purple theme matching OverlordAI brand.

**Tech Stack:** Next.js 14, React 18, Tailwind CSS, react-three-fiber, @react-three/drei, Framer Motion, Lucide React

---

## Task 1: Install Three.js Dependencies

**Files:**
- Modify: `packages/ui/package.json`

**Step 1: Install react-three-fiber and dependencies**

Run:
```bash
cd /Users/johnferry/Documents/GitHub/open-forge/.worktrees/landing-page/packages/ui
npm install three @react-three/fiber @react-three/drei framer-motion --save
npm install @types/three --save-dev
```

Expected: Package.json updated with new dependencies

**Step 2: Verify installation**

Run: `npm ls three @react-three/fiber`
Expected: Shows installed versions without errors

**Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "feat(landing): add Three.js and Framer Motion dependencies"
```

---

## Task 2: Create Marketing Route Group Structure

**Files:**
- Create: `packages/ui/src/app/(marketing)/layout.tsx`
- Create: `packages/ui/src/app/(marketing)/page.tsx`

**Step 1: Create marketing layout**

Create `packages/ui/src/app/(marketing)/layout.tsx`:

```tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Open Forge | The Open Source Ontology Platform',
  description:
    'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in. Apache 2.0 licensed.',
  openGraph: {
    title: 'Open Forge | The Open Source Ontology Platform',
    description:
      'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in.',
    type: 'website',
    url: 'https://forge.overlordai.ai',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Open Forge | The Open Source Ontology Platform',
    description:
      'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required.',
  },
};

interface MarketingLayoutProps {
  children: React.ReactNode;
}

export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      {children}
    </div>
  );
}
```

**Step 2: Create placeholder landing page**

Create `packages/ui/src/app/(marketing)/page.tsx`:

```tsx
export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      <h1 className="text-4xl font-bold text-center py-20">
        Open Forge Landing Page
      </h1>
    </main>
  );
}
```

**Step 3: Verify page loads**

Run: `npm run dev`
Navigate to: http://localhost:3000
Expected: See "Open Forge Landing Page" with dark background

**Step 4: Commit**

```bash
git add src/app/\(marketing\)/
git commit -m "feat(landing): create marketing route group structure"
```

---

## Task 3: Create Shared Landing Page Components - Navigation

**Files:**
- Create: `packages/ui/src/components/marketing/MarketingNav.tsx`

**Step 1: Create navigation component**

Create `packages/ui/src/components/marketing/MarketingNav.tsx`:

```tsx
'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Menu, X, Github } from 'lucide-react';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '#features', label: 'Features' },
  { href: '#architecture', label: 'Architecture' },
  { href: 'https://github.com/overlordai/open-forge', label: 'GitHub', external: true },
  { href: '/docs', label: 'Docs' },
];

export function MarketingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600" />
          <span className="text-xl font-bold">Open Forge</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              target={link.external ? '_blank' : undefined}
              rel={link.external ? 'noopener noreferrer' : undefined}
              className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="https://github.com/overlordai/open-forge"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium hover:bg-zinc-700 transition-colors"
          >
            <Github className="h-4 w-4" />
            Star on GitHub
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-zinc-800 bg-zinc-950 px-6 py-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              target={link.external ? '_blank' : undefined}
              className="block py-3 text-zinc-400 hover:text-zinc-50"
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
```

**Step 2: Create component index**

Create `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add marketing navigation component"
```

---

## Task 4: Create Hero Section

**Files:**
- Create: `packages/ui/src/components/marketing/HeroSection.tsx`

**Step 1: Create hero section**

Create `packages/ui/src/components/marketing/HeroSection.tsx`:

```tsx
import Link from 'next/link';
import { Github, ArrowRight, Rocket } from 'lucide-react';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-violet-950/20 via-zinc-950 to-zinc-950" />

      {/* Animated grid background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgb(139 92 246 / 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgb(139 92 246 / 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
        {/* Badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-500" />
          </span>
          20+ Autonomous Agents | 6 Agent Clusters | Apache 2.0 Licensed
        </div>

        {/* Headline */}
        <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
          <span className="text-zinc-50">The </span>
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent">
            Open Source
          </span>
          <br />
          <span className="text-zinc-50">Ontology Platform</span>
        </h1>

        {/* Subheadline */}
        <p className="mx-auto mb-8 max-w-2xl text-lg text-zinc-400 sm:text-xl">
          Enterprise-grade data infrastructure with autonomous AI agents.{' '}
          <span className="text-zinc-200">No consultants required.</span>{' '}
          <span className="text-zinc-200">No vendor lock-in.</span>{' '}
          Your ontology, your operations, your code.
        </p>

        {/* Value proposition */}
        <p className="mx-auto mb-12 max-w-xl text-base text-zinc-500">
          Why pay millions for proprietary platforms and forward-deployed engineers when
          autonomous agents can build, integrate, and operate your data infrastructure 24/7?
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="https://github.com/overlordai/open-forge"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2 rounded-lg bg-violet-600 px-6 py-3 text-base font-semibold text-white hover:bg-violet-500 transition-colors"
          >
            <Github className="h-5 w-5" />
            Star on GitHub
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="#get-started"
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800/50 px-6 py-3 text-base font-semibold text-zinc-50 hover:bg-zinc-800 transition-colors"
          >
            <Rocket className="h-5 w-5" />
            Deploy Now
          </Link>
          <Link
            href="#contact"
            className="flex items-center gap-2 rounded-lg border border-zinc-800 px-6 py-3 text-base font-semibold text-zinc-400 hover:text-zinc-50 hover:border-zinc-700 transition-colors"
          >
            Request Demo
          </Link>
        </div>

        {/* Social proof strip */}
        <div className="mt-16 flex flex-wrap items-center justify-center gap-8 text-sm text-zinc-500">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span>10 Packages</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-violet-500" />
            <span>20+ Agents</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-blue-500" />
            <span>50+ API Endpoints</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-purple-500" />
            <span>4 Code Generators</span>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add hero section with gradient styling"
```

---

## Task 5: Create Problem Section (Anti-FDE Manifesto)

**Files:**
- Create: `packages/ui/src/components/marketing/ProblemSection.tsx`

**Step 1: Create problem section**

Create `packages/ui/src/components/marketing/ProblemSection.tsx`:

```tsx
import { ArrowRight } from 'lucide-react';

const contrasts = [
  { old: 'Proprietary ontology platform', new: 'Open source ontology engine' },
  { old: 'Forward-deployed engineers', new: 'Autonomous agent clusters' },
  { old: 'Years to value', new: 'Days to deployment' },
  { old: 'Vendor lock-in', new: 'Apache 2.0 licensed' },
  { old: 'Black box operations', new: 'Transparent, auditable code' },
  { old: '$10M+ annual contracts', new: 'Self-hosted, free forever' },
];

export function ProblemSection() {
  return (
    <section className="relative py-24 overflow-hidden" id="problem">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950" />

      <div className="relative z-10 mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            The $10M Question
          </h2>
        </div>

        {/* Problem narrative */}
        <div className="mb-16 space-y-6 text-center">
          <p className="text-xl text-zinc-300">
            Enterprise data platforms promised transformation.{' '}
            <span className="text-zinc-50 font-semibold">They delivered dependency.</span>
          </p>

          <p className="text-lg text-zinc-400 max-w-3xl mx-auto">
            You wanted an operating system for your business. You got a consulting engagement
            that never ends. You wanted to run your business as code. You got a team of
            forward-deployed engineers running it for you—at{' '}
            <span className="text-violet-400 font-semibold">$500K per head, per year.</span>
          </p>

          <p className="text-lg text-zinc-400 max-w-3xl mx-auto">
            The dirty secret? The "ontology" they sold you—the semantic layer connecting
            your data to decisions—isn't magic. It's engineering. Engineering that{' '}
            <span className="text-zinc-200">autonomous AI agents</span> can now perform
            faster, cheaper, and without the billable hours.
          </p>
        </div>

        {/* Contrast grid */}
        <div className="mb-16 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-8">
          <div className="grid gap-4">
            {contrasts.map((item, index) => (
              <div
                key={index}
                className="grid grid-cols-[1fr,auto,1fr] items-center gap-4 rounded-lg bg-zinc-800/30 p-4"
              >
                <div className="text-right">
                  <span className="text-zinc-500 line-through">{item.old}</span>
                </div>
                <ArrowRight className="h-5 w-5 text-violet-500 flex-shrink-0" />
                <div>
                  <span className="text-zinc-50 font-medium">{item.new}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Closing line */}
        <p className="text-center text-2xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
          The era of indentured data platforms is over.
        </p>
      </div>
    </section>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
export { ProblemSection } from './ProblemSection';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add problem section with anti-FDE messaging"
```

---

## Task 6: Create Three.js Animation Base Components

**Files:**
- Create: `packages/ui/src/components/marketing/three/CanvasWrapper.tsx`
- Create: `packages/ui/src/components/marketing/three/index.ts`

**Step 1: Create canvas wrapper for Three.js**

Create `packages/ui/src/components/marketing/three/CanvasWrapper.tsx`:

```tsx
'use client';

import { Canvas } from '@react-three/fiber';
import { Suspense, type ReactNode } from 'react';

interface CanvasWrapperProps {
  children: ReactNode;
  className?: string;
}

export function CanvasWrapper({ children, className }: CanvasWrapperProps) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          {children}
        </Suspense>
      </Canvas>
    </div>
  );
}
```

**Step 2: Create index export**

Create `packages/ui/src/components/marketing/three/index.ts`:

```tsx
export { CanvasWrapper } from './CanvasWrapper';
```

**Step 3: Commit**

```bash
git add src/components/marketing/three/
git commit -m "feat(landing): add Three.js canvas wrapper component"
```

---

## Task 7: Create Ontology Graph Animation

**Files:**
- Create: `packages/ui/src/components/marketing/three/OntologyAnimation.tsx`

**Step 1: Create ontology graph animation**

Create `packages/ui/src/components/marketing/three/OntologyAnimation.tsx`:

```tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Sphere, Line } from '@react-three/drei';
import * as THREE from 'three';

interface NodeData {
  position: [number, number, number];
  color: string;
  label: string;
}

const nodes: NodeData[] = [
  { position: [0, 0, 0], color: '#8b5cf6', label: 'Ontology' },
  { position: [1.5, 1, 0.5], color: '#a78bfa', label: 'Customer' },
  { position: [-1.5, 1, -0.5], color: '#a78bfa', label: 'Order' },
  { position: [1.5, -1, -0.5], color: '#a78bfa', label: 'Product' },
  { position: [-1.5, -1, 0.5], color: '#a78bfa', label: 'Invoice' },
  { position: [0, 1.8, 0], color: '#c4b5fd', label: 'Schema' },
];

const edges: [number, number][] = [
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
  [1, 2], [2, 3], [3, 4], [4, 1], [1, 5], [2, 5],
];

function GraphNode({ position, color }: { position: [number, number, number]; color: string }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 2) * 0.05);
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.3}>
      <Sphere ref={ref} args={[0.15, 32, 32]} position={position}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
          roughness={0.3}
          metalness={0.8}
        />
      </Sphere>
    </Float>
  );
}

function GraphEdge({ start, end }: { start: [number, number, number]; end: [number, number, number] }) {
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end]);

  return (
    <Line
      points={points}
      color="#8b5cf6"
      lineWidth={1}
      opacity={0.4}
      transparent
    />
  );
}

export function OntologyAnimation() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => (
        <GraphNode key={i} position={node.position} color={node.color} />
      ))}
      {edges.map(([startIdx, endIdx], i) => (
        <GraphEdge
          key={i}
          start={nodes[startIdx].position}
          end={nodes[endIdx].position}
        />
      ))}
    </group>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/three/index.ts`:

```tsx
export { CanvasWrapper } from './CanvasWrapper';
export { OntologyAnimation } from './OntologyAnimation';
```

**Step 3: Commit**

```bash
git add src/components/marketing/three/
git commit -m "feat(landing): add ontology graph Three.js animation"
```

---

## Task 8: Create Agent Swarm Animation

**Files:**
- Create: `packages/ui/src/components/marketing/three/AgentSwarmAnimation.tsx`

**Step 1: Create agent swarm animation**

Create `packages/ui/src/components/marketing/three/AgentSwarmAnimation.tsx`:

```tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Trail } from '@react-three/drei';
import * as THREE from 'three';

const clusterColors = [
  '#8b5cf6', // violet - Discovery
  '#a78bfa', // light violet - Data Architect
  '#7c3aed', // purple - App Builder
  '#06b6d4', // cyan - Operations
  '#c4b5fd', // lavender - Enablement
  '#6366f1', // indigo - Orchestration
];

function Agent({
  clusterIndex,
  agentIndex,
  totalInCluster
}: {
  clusterIndex: number;
  agentIndex: number;
  totalInCluster: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const color = clusterColors[clusterIndex % clusterColors.length];

  const initialAngle = (agentIndex / totalInCluster) * Math.PI * 2;
  const clusterAngle = (clusterIndex / 6) * Math.PI * 2;
  const clusterRadius = 1.2;
  const orbitRadius = 0.3 + (agentIndex % 3) * 0.15;

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.elapsedTime;
      const speed = 0.5 + (agentIndex % 3) * 0.2;

      // Cluster center position
      const cx = Math.cos(clusterAngle + time * 0.1) * clusterRadius;
      const cy = Math.sin(time * 0.2 + clusterIndex) * 0.3;
      const cz = Math.sin(clusterAngle + time * 0.1) * clusterRadius;

      // Agent orbit around cluster
      const ax = Math.cos(initialAngle + time * speed) * orbitRadius;
      const ay = Math.sin(time * speed * 0.5) * 0.1;
      const az = Math.sin(initialAngle + time * speed) * orbitRadius;

      ref.current.position.set(cx + ax, cy + ay, cz + az);

      // Pulsing scale
      const pulse = 1 + Math.sin(time * 3 + agentIndex) * 0.1;
      ref.current.scale.setScalar(pulse);
    }
  });

  return (
    <Trail
      width={0.5}
      length={4}
      color={color}
      attenuation={(t) => t * t}
    >
      <Sphere ref={ref} args={[0.05, 16, 16]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.8}
          roughness={0.2}
          metalness={0.9}
        />
      </Sphere>
    </Trail>
  );
}

export function AgentSwarmAnimation() {
  const groupRef = useRef<THREE.Group>(null);

  // Generate agents per cluster
  const agents = useMemo(() => {
    const result: { clusterIndex: number; agentIndex: number; total: number }[] = [];
    const agentsPerCluster = [4, 3, 4, 4, 3, 3]; // Different sizes per cluster

    agentsPerCluster.forEach((count, clusterIdx) => {
      for (let i = 0; i < count; i++) {
        result.push({ clusterIndex: clusterIdx, agentIndex: i, total: count });
      }
    });

    return result;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      // Gentle breathing effect
      const scale = 1 + Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
      groupRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group ref={groupRef}>
      {agents.map((agent, i) => (
        <Agent
          key={i}
          clusterIndex={agent.clusterIndex}
          agentIndex={agent.agentIndex}
          totalInCluster={agent.total}
        />
      ))}
    </group>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/three/index.ts`:

```tsx
export { CanvasWrapper } from './CanvasWrapper';
export { OntologyAnimation } from './OntologyAnimation';
export { AgentSwarmAnimation } from './AgentSwarmAnimation';
```

**Step 3: Commit**

```bash
git add src/components/marketing/three/
git commit -m "feat(landing): add agent swarm Three.js animation"
```

---

## Task 9: Create Code Loop Animation

**Files:**
- Create: `packages/ui/src/components/marketing/three/CodeLoopAnimation.tsx`

**Step 1: Create code loop animation**

Create `packages/ui/src/components/marketing/three/CodeLoopAnimation.tsx`:

```tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Torus, Sphere } from '@react-three/drei';
import * as THREE from 'three';

function CodeParticle({ index, total }: { index: number; total: number }) {
  const ref = useRef<THREE.Mesh>(null);
  const initialAngle = (index / total) * Math.PI * 2;

  // Alternate between green (pass) and amber (refine)
  const isPass = index % 5 !== 0;
  const color = isPass ? '#22c55e' : '#f59e0b';

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.elapsedTime;
      const speed = 0.3;
      const angle = initialAngle + time * speed;

      // Möbius-like path on torus
      const R = 1.2; // Major radius
      const r = 0.4; // Minor radius
      const twist = angle * 0.5;

      const x = (R + r * Math.cos(twist)) * Math.cos(angle);
      const y = r * Math.sin(twist);
      const z = (R + r * Math.cos(twist)) * Math.sin(angle);

      ref.current.position.set(x, y, z);

      // Pulse when passing validation point
      const atCheckpoint = Math.abs(Math.sin(angle * 2)) < 0.1;
      const scale = atCheckpoint ? 1.5 : 1;
      ref.current.scale.setScalar(scale);
    }
  });

  return (
    <Sphere ref={ref} args={[0.06, 16, 16]}>
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.7}
        roughness={0.3}
        metalness={0.7}
      />
    </Sphere>
  );
}

export function CodeLoopAnimation() {
  const groupRef = useRef<THREE.Group>(null);
  const particleCount = 15;

  const particles = useMemo(() =>
    Array.from({ length: particleCount }, (_, i) => i),
    []
  );

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
      groupRef.current.rotation.z = Math.cos(state.clock.elapsedTime * 0.15) * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Loop track */}
      <Torus args={[1.2, 0.02, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color="#8b5cf6"
          emissive="#8b5cf6"
          emissiveIntensity={0.3}
          transparent
          opacity={0.6}
        />
      </Torus>

      {/* Code particles */}
      {particles.map((i) => (
        <CodeParticle key={i} index={i} total={particleCount} />
      ))}
    </group>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/three/index.ts`:

```tsx
export { CanvasWrapper } from './CanvasWrapper';
export { OntologyAnimation } from './OntologyAnimation';
export { AgentSwarmAnimation } from './AgentSwarmAnimation';
export { CodeLoopAnimation } from './CodeLoopAnimation';
```

**Step 3: Commit**

```bash
git add src/components/marketing/three/
git commit -m "feat(landing): add code loop Three.js animation"
```

---

## Task 10: Create Timeline Compression Animation

**Files:**
- Create: `packages/ui/src/components/marketing/three/TimelineAnimation.tsx`

**Step 1: Create timeline animation**

Create `packages/ui/src/components/marketing/three/TimelineAnimation.tsx`:

```tsx
'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Box, Text } from '@react-three/drei';
import * as THREE from 'three';

function TimelineBlock({
  label,
  index,
  total
}: {
  label: string;
  index: number;
  total: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const textRef = useRef<THREE.Mesh>(null);
  const initialX = (index - total / 2) * 0.8;

  useFrame((state) => {
    if (ref.current && textRef.current) {
      const time = state.clock.elapsedTime;
      const cycleTime = 4; // 4 second cycle
      const t = (time % cycleTime) / cycleTime;

      // Compression phase (0 to 0.5): blocks move toward center
      // Expansion phase (0.5 to 1): blocks spread back out
      let compressionFactor: number;
      if (t < 0.4) {
        // Compress
        compressionFactor = 1 - (t / 0.4) * 0.9;
      } else if (t < 0.6) {
        // Hold compressed
        compressionFactor = 0.1;
      } else {
        // Expand back
        compressionFactor = 0.1 + ((t - 0.6) / 0.4) * 0.9;
      }

      const x = initialX * compressionFactor;
      ref.current.position.x = x;
      textRef.current.position.x = x;

      // Scale based on whether it's "Day 1" (last block)
      const isDay1 = index === total - 1;
      if (isDay1 && t > 0.35 && t < 0.65) {
        ref.current.scale.setScalar(1.5);
        // @ts-ignore
        ref.current.material.emissiveIntensity = 1;
      } else {
        ref.current.scale.setScalar(1);
        // @ts-ignore
        ref.current.material.emissiveIntensity = 0.3;
      }
    }
  });

  const color = index === 3 ? '#22c55e' : '#8b5cf6';

  return (
    <group>
      <Box ref={ref} args={[0.5, 0.3, 0.1]} position={[initialX, 0, 0]}>
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.3}
          roughness={0.4}
          metalness={0.6}
        />
      </Box>
      <Text
        ref={textRef}
        position={[initialX, 0, 0.1]}
        fontSize={0.1}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}

export function TimelineAnimation() {
  const groupRef = useRef<THREE.Group>(null);
  const labels = ['Year 1', 'Year 2', 'Year 3', 'Day 1'];

  return (
    <group ref={groupRef}>
      {labels.map((label, i) => (
        <TimelineBlock
          key={i}
          label={label}
          index={i}
          total={labels.length}
        />
      ))}
    </group>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/three/index.ts`:

```tsx
export { CanvasWrapper } from './CanvasWrapper';
export { OntologyAnimation } from './OntologyAnimation';
export { AgentSwarmAnimation } from './AgentSwarmAnimation';
export { CodeLoopAnimation } from './CodeLoopAnimation';
export { TimelineAnimation } from './TimelineAnimation';
```

**Step 3: Commit**

```bash
git add src/components/marketing/three/
git commit -m "feat(landing): add timeline compression Three.js animation"
```

---

## Task 11: Create Capability Cards Section

**Files:**
- Create: `packages/ui/src/components/marketing/CapabilityCards.tsx`

**Step 1: Create capability cards with Three.js backgrounds**

Create `packages/ui/src/components/marketing/CapabilityCards.tsx`:

```tsx
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
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
export { ProblemSection } from './ProblemSection';
export { CapabilityCards } from './CapabilityCards';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add capability cards with Three.js animations"
```

---

## Task 12: Create Audience Segments Section

**Files:**
- Create: `packages/ui/src/components/marketing/AudienceSegments.tsx`

**Step 1: Create tabbed audience sections**

Create `packages/ui/src/components/marketing/AudienceSegments.tsx`:

```tsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Code2, Building2, Crown, Github, FileText, Rocket, Users, BarChart3, Mail } from 'lucide-react';
import { cn } from '@/lib/utils';

type AudienceKey = 'engineers' | 'leaders' | 'executives';

interface AudienceData {
  key: AudienceKey;
  icon: React.ElementType;
  label: string;
  headline: string;
  body: string[];
  ctas: { label: string; href: string; icon: React.ElementType; primary?: boolean }[];
}

const audiences: AudienceData[] = [
  {
    key: 'engineers',
    icon: Code2,
    label: 'For Engineers',
    headline: 'Own the Code That Runs the World',
    body: [
      'The platforms that power Fortune 500 data operations shouldn\'t be proprietary black boxes. Open Forge is the ontology platform built in the open—Python, TypeScript, LangGraph, FastAPI, React—modern stack, MIT-educated architecture, Apache 2.0 licensed.',
      'This isn\'t a toy. It\'s 80,000+ lines of production code across 10 packages: ontology compilers, connector frameworks, pipeline engines, agent orchestration, human-in-the-loop workflows, and full-stack code generation.',
      'The proprietary platforms had a 20-year head start. We have a community.',
    ],
    ctas: [
      { label: 'Star on GitHub', href: 'https://github.com/overlordai/open-forge', icon: Github, primary: true },
      { label: 'Read the Architecture', href: '/docs/architecture', icon: FileText },
      { label: 'First Good Issues', href: 'https://github.com/overlordai/open-forge/issues?q=is:issue+is:open+label:"good+first+issue"', icon: Code2 },
    ],
  },
  {
    key: 'leaders',
    icon: Building2,
    label: 'For Technical Leaders',
    headline: 'Your Data Platform. Your Rules.',
    body: [
      'Stop renting your data infrastructure. Open Forge deploys on your cloud, your Kubernetes cluster, your terms. Connect to PostgreSQL, MySQL, S3, REST APIs, GraphQL endpoints—50+ connector types with schema discovery built in.',
      'The ontology layer you define is portable. The pipelines are Dagster-native. The APIs are standard REST and GraphQL. When you need to change direction, you change direction—no exit negotiations, no migration fees, no hostage situations.',
    ],
    ctas: [
      { label: 'Deploy on Your Infrastructure', href: '/docs/deploy', icon: Rocket, primary: true },
      { label: 'View Connectors', href: '/docs/connectors', icon: Users },
      { label: 'Book Architecture Review', href: '/contact?type=architecture', icon: Building2 },
    ],
  },
  {
    key: 'executives',
    icon: Crown,
    label: 'For Executives',
    headline: 'AI Transformation Without the Tribute',
    body: [
      'Your competitors are spending $10M+ annually on proprietary platforms and armies of consultants. You can deploy the same ontology-powered, AI-operated infrastructure—and own it outright.',
      'Open Forge\'s autonomous agents replace the forward-deployed engineer model entirely. Discovery agents interview stakeholders. Architect agents design schemas. Builder agents generate applications. Operations agents monitor and scale. 24/7, no billable hours.',
      'This is AI enablement without indentured servitude.',
    ],
    ctas: [
      { label: 'Request Executive Briefing', href: '/contact?type=executive', icon: Mail, primary: true },
      { label: 'View ROI Calculator', href: '/roi', icon: BarChart3 },
      { label: 'Compare to Alternatives', href: '/compare', icon: FileText },
    ],
  },
];

export function AudienceSegments() {
  const [activeTab, setActiveTab] = useState<AudienceKey>('engineers');
  const activeAudience = audiences.find((a) => a.key === activeTab)!;

  return (
    <section className="relative py-24 bg-zinc-900/50" id="audiences">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            Built For Everyone Who's Had Enough
          </h2>
        </div>

        {/* Tabs */}
        <div className="mb-8 flex justify-center">
          <div className="inline-flex rounded-lg border border-zinc-800 bg-zinc-900 p-1">
            {audiences.map((audience) => {
              const Icon = audience.icon;
              return (
                <button
                  key={audience.key}
                  onClick={() => setActiveTab(audience.key)}
                  className={cn(
                    'flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
                    activeTab === audience.key
                      ? 'bg-violet-600 text-white'
                      : 'text-zinc-400 hover:text-zinc-50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{audience.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-8 md:p-12">
          <h3 className="mb-6 text-3xl font-bold text-zinc-50">
            {activeAudience.headline}
          </h3>

          <div className="mb-8 space-y-4">
            {activeAudience.body.map((paragraph, i) => (
              <p key={i} className="text-lg text-zinc-400 leading-relaxed">
                {paragraph}
              </p>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex flex-wrap gap-4">
            {activeAudience.ctas.map((cta) => {
              const Icon = cta.icon;
              return (
                <Link
                  key={cta.label}
                  href={cta.href}
                  target={cta.href.startsWith('http') ? '_blank' : undefined}
                  rel={cta.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className={cn(
                    'flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium transition-colors',
                    cta.primary
                      ? 'bg-violet-600 text-white hover:bg-violet-500'
                      : 'border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {cta.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
export { ProblemSection } from './ProblemSection';
export { CapabilityCards } from './CapabilityCards';
export { AudienceSegments } from './AudienceSegments';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add audience segments with tabbed navigation"
```

---

## Task 13: Create Architecture Section

**Files:**
- Create: `packages/ui/src/components/marketing/ArchitectureSection.tsx`

**Step 1: Create architecture diagram section**

Create `packages/ui/src/components/marketing/ArchitectureSection.tsx`:

```tsx
import { ExternalLink } from 'lucide-react';
import Link from 'next/link';

const layers = [
  { name: 'UI Portal', tech: 'React / Next.js', color: 'bg-violet-500' },
  { name: 'API Gateway', tech: 'FastAPI + GraphQL + SSE', color: 'bg-purple-500' },
  {
    name: 'Agent Clusters',
    items: ['Discovery', 'Data Architect', 'App Builder', 'Operations'],
    color: 'bg-indigo-500'
  },
  { name: 'Agent Framework', tech: 'LangGraph', color: 'bg-blue-500' },
  {
    name: 'Core Engines',
    items: ['Ontology Engine', 'Codegen Engine', 'Pipeline Engine'],
    color: 'bg-cyan-500'
  },
  { name: 'Connectors', tech: 'PostgreSQL, S3, REST, GraphQL...', color: 'bg-teal-500' },
];

const stats = [
  { label: '10 Packages', value: '10' },
  { label: '20+ Agents', value: '20+' },
  { label: '50+ Endpoints', value: '50+' },
  { label: '7 Connectors', value: '7' },
  { label: '4 Generators', value: '4' },
];

export function ArchitectureSection() {
  return (
    <section className="relative py-24" id="architecture">
      <div className="mx-auto max-w-5xl px-6">
        {/* Section header */}
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            Full Stack.{' '}
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Open Source.
            </span>{' '}
            Production Ready.
          </h2>
        </div>

        {/* Architecture diagram */}
        <div className="mb-12 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 md:p-8">
          <div className="space-y-3">
            {layers.map((layer, index) => (
              <div
                key={layer.name}
                className="group relative overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800/50 p-4 transition-all hover:border-violet-500/50"
              >
                {/* Color indicator */}
                <div className={`absolute left-0 top-0 bottom-0 w-1 ${layer.color}`} />

                <div className="ml-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <span className="font-semibold text-zinc-50">{layer.name}</span>
                  {'tech' in layer && (
                    <span className="text-sm text-zinc-500">{layer.tech}</span>
                  )}
                  {'items' in layer && (
                    <div className="flex flex-wrap gap-2">
                      {layer.items.map((item) => (
                        <span
                          key={item}
                          className="rounded-full bg-zinc-700/50 px-3 py-1 text-xs text-zinc-300"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Connection line to next layer */}
                {index < layers.length - 1 && (
                  <div className="absolute left-6 -bottom-3 h-3 w-px bg-zinc-700" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Stats strip */}
        <div className="mb-8 flex flex-wrap justify-center gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-violet-400">{stat.value}</div>
              <div className="text-sm text-zinc-500">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="text-center">
          <Link
            href="/docs/architecture"
            className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 transition-colors"
          >
            Explore the Full Architecture
            <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
export { ProblemSection } from './ProblemSection';
export { CapabilityCards } from './CapabilityCards';
export { AudienceSegments } from './AudienceSegments';
export { ArchitectureSection } from './ArchitectureSection';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add architecture diagram section"
```

---

## Task 14: Create Footer CTA Section

**Files:**
- Create: `packages/ui/src/components/marketing/FooterCTA.tsx`

**Step 1: Create footer CTA section**

Create `packages/ui/src/components/marketing/FooterCTA.tsx`:

```tsx
import Link from 'next/link';
import { Github, BookOpen, Mail, ExternalLink } from 'lucide-react';

const ctaCards = [
  {
    title: 'Contribute',
    description: 'Join engineers building the open alternative',
    cta: 'Star on GitHub',
    href: 'https://github.com/overlordai/open-forge',
    icon: Github,
  },
  {
    title: 'Deploy',
    description: 'Get running on your infrastructure today',
    cta: 'Quick Start Guide',
    href: '/docs/quickstart',
    icon: BookOpen,
  },
  {
    title: 'Connect',
    description: 'Talk to our team about your use case',
    cta: 'Request Demo',
    href: '/contact',
    icon: Mail,
  },
];

const footerLinks = {
  Product: [
    { label: 'Documentation', href: '/docs' },
    { label: 'Architecture', href: '/docs/architecture' },
    { label: 'Quick Start', href: '/docs/quickstart' },
    { label: 'Roadmap', href: '/roadmap' },
  ],
  Community: [
    { label: 'GitHub', href: 'https://github.com/overlordai/open-forge', external: true },
    { label: 'Discord', href: 'https://discord.gg/overlordai', external: true },
    { label: 'Twitter/X', href: 'https://twitter.com/overlordai', external: true },
    { label: 'Blog', href: '/blog' },
  ],
  Company: [
    { label: 'About OverlordAI', href: 'https://overlordai.ai', external: true },
    { label: 'Contact', href: '/contact' },
    { label: 'Careers', href: '/careers' },
  ],
};

const siblingProducts = [
  { name: 'Overlord', href: 'https://app.overlordai.ai' },
  { name: 'Wisdom', href: 'https://wisdom.overlordai.ai' },
  { name: 'Anthill', href: 'https://anthill.overlordai.ai' },
];

export function FooterCTA() {
  return (
    <footer className="relative border-t border-zinc-800 bg-zinc-950">
      {/* CTA Section */}
      <section className="py-24" id="get-started">
        <div className="mx-auto max-w-5xl px-6">
          {/* Header */}
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-4xl font-bold bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent sm:text-5xl">
              The Forge Is Open
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Whether you're an engineer ready to build, a leader ready to deploy, or an
              executive ready to break free—the platform is here. Open source. Self-hosted. Autonomous.
            </p>
          </div>

          {/* CTA Cards */}
          <div className="grid gap-6 md:grid-cols-3 mb-16">
            {ctaCards.map((card) => {
              const Icon = card.icon;
              return (
                <Link
                  key={card.title}
                  href={card.href}
                  target={card.href.startsWith('http') ? '_blank' : undefined}
                  rel={card.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className="group rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50 hover:bg-zinc-900"
                >
                  <Icon className="mb-4 h-8 w-8 text-violet-500" />
                  <h3 className="mb-2 text-xl font-semibold text-zinc-50">{card.title}</h3>
                  <p className="mb-4 text-sm text-zinc-400">{card.description}</p>
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-violet-400 group-hover:text-violet-300">
                    {card.cta}
                    <ExternalLink className="h-3 w-3" />
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer Links */}
      <div className="border-t border-zinc-800">
        <div className="mx-auto max-w-5xl px-6 py-12">
          <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
            {/* Logo and tagline */}
            <div>
              <Link href="/" className="flex items-center gap-2 mb-4">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600" />
                <span className="text-xl font-bold text-zinc-50">Open Forge</span>
              </Link>
              <p className="text-sm text-zinc-500">
                The open source ontology platform.
              </p>
            </div>

            {/* Link columns */}
            {Object.entries(footerLinks).map(([category, links]) => (
              <div key={category}>
                <h4 className="mb-4 text-sm font-semibold text-zinc-50">{category}</h4>
                <ul className="space-y-2">
                  {links.map((link) => (
                    <li key={link.label}>
                      <Link
                        href={link.href}
                        target={link.external ? '_blank' : undefined}
                        rel={link.external ? 'noopener noreferrer' : undefined}
                        className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Brand footer */}
          <div className="mt-12 pt-8 border-t border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-zinc-500">
              Part of the{' '}
              <Link href="https://overlordai.ai" className="text-zinc-300 hover:text-zinc-50">
                OverlordAI
              </Link>{' '}
              family:{' '}
              {siblingProducts.map((product, i) => (
                <span key={product.name}>
                  <Link
                    href={product.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-zinc-50"
                  >
                    {product.name}
                  </Link>
                  {i < siblingProducts.length - 1 ? ' · ' : ''}
                </span>
              ))}
              {' · '}
              <span className="text-violet-400 font-medium">Forge</span>
            </p>
            <p className="text-sm text-zinc-600">
              © {new Date().getFullYear()} OverlordAI. Apache 2.0 Licensed.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
```

**Step 2: Export from index**

Update `packages/ui/src/components/marketing/index.ts`:

```tsx
export { MarketingNav } from './MarketingNav';
export { HeroSection } from './HeroSection';
export { ProblemSection } from './ProblemSection';
export { CapabilityCards } from './CapabilityCards';
export { AudienceSegments } from './AudienceSegments';
export { ArchitectureSection } from './ArchitectureSection';
export { FooterCTA } from './FooterCTA';
```

**Step 3: Commit**

```bash
git add src/components/marketing/
git commit -m "feat(landing): add footer CTA section with OverlordAI branding"
```

---

## Task 15: Assemble Complete Landing Page

**Files:**
- Modify: `packages/ui/src/app/(marketing)/page.tsx`
- Modify: `packages/ui/src/app/(marketing)/layout.tsx`

**Step 1: Update layout to include navigation**

Update `packages/ui/src/app/(marketing)/layout.tsx`:

```tsx
import type { Metadata } from 'next';
import { MarketingNav } from '@/components/marketing';

export const metadata: Metadata = {
  title: 'Open Forge | The Open Source Ontology Platform',
  description:
    'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in. Apache 2.0 licensed.',
  openGraph: {
    title: 'Open Forge | The Open Source Ontology Platform',
    description:
      'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in.',
    type: 'website',
    url: 'https://forge.overlordai.ai',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Open Forge | The Open Source Ontology Platform',
    description:
      'Enterprise-grade data infrastructure with autonomous AI agents. No consultants required.',
  },
};

interface MarketingLayoutProps {
  children: React.ReactNode;
}

export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <MarketingNav />
      {children}
    </div>
  );
}
```

**Step 2: Assemble landing page**

Update `packages/ui/src/app/(marketing)/page.tsx`:

```tsx
import {
  HeroSection,
  ProblemSection,
  CapabilityCards,
  AudienceSegments,
  ArchitectureSection,
  FooterCTA,
} from '@/components/marketing';

export default function LandingPage() {
  return (
    <main className="flex flex-col">
      <HeroSection />
      <ProblemSection />
      <CapabilityCards />
      <AudienceSegments />
      <ArchitectureSection />
      <FooterCTA />
    </main>
  );
}
```

**Step 3: Verify page renders**

Run: `npm run dev`
Navigate to: http://localhost:3000
Expected: Full landing page renders with all sections

**Step 4: Commit**

```bash
git add src/app/\(marketing\)/
git commit -m "feat(landing): assemble complete landing page"
```

---

## Task 16: Add Reduced Motion Support

**Files:**
- Modify: `packages/ui/src/components/marketing/CapabilityCards.tsx`

**Step 1: Add useReducedMotion hook**

Create `packages/ui/src/lib/hooks/use-reduced-motion.ts`:

```tsx
'use client';

import { useEffect, useState } from 'react';

export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}
```

**Step 2: Export from hooks index**

Update `packages/ui/src/lib/hooks/index.ts` to add:

```tsx
export { useReducedMotion } from './use-reduced-motion';
```

**Step 3: Update CapabilityCards to respect reduced motion**

Update the `CapabilityCard` function in `packages/ui/src/components/marketing/CapabilityCards.tsx`:

```tsx
'use client';

import { Suspense } from 'react';
import { useReducedMotion } from '@/lib/hooks/use-reduced-motion';
import { CanvasWrapper, OntologyAnimation, AgentSwarmAnimation, CodeLoopAnimation, TimelineAnimation } from './three';

// ... rest of file stays the same, but update CapabilityCard:

function CapabilityCard({ title, description, animation }: CapabilityCardProps) {
  const prefersReducedMotion = useReducedMotion();

  const AnimationComponent = {
    ontology: OntologyAnimation,
    swarm: AgentSwarmAnimation,
    codeloop: CodeLoopAnimation,
    timeline: TimelineAnimation,
  }[animation];

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50 hover:bg-zinc-900">
      {/* Three.js Background - only render if motion is OK */}
      {!prefersReducedMotion && (
        <div className="absolute inset-0 opacity-30 group-hover:opacity-50 transition-opacity">
          <Suspense fallback={null}>
            <CanvasWrapper className="h-full w-full">
              <AnimationComponent />
            </CanvasWrapper>
          </Suspense>
        </div>
      )}

      {/* Static gradient fallback when motion is reduced */}
      {prefersReducedMotion && (
        <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-violet-500/20 to-purple-500/20" />
      )}

      {/* Content */}
      <div className="relative z-10">
        <h3 className="mb-3 text-xl font-semibold text-zinc-50">{title}</h3>
        <p className="text-sm text-zinc-400 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add src/lib/hooks/ src/components/marketing/
git commit -m "feat(landing): add reduced motion accessibility support"
```

---

## Task 17: Build and Test

**Step 1: Run type check**

Run: `npm run type-check`
Expected: No type errors

**Step 2: Run linter**

Run: `npm run lint`
Expected: No lint errors (or only minor warnings)

**Step 3: Run build**

Run: `npm run build`
Expected: Build completes successfully

**Step 4: Test production build**

Run: `npm run start`
Navigate to: http://localhost:3000
Expected: Landing page works in production mode

**Step 5: Commit any fixes**

If fixes were needed:
```bash
git add -A
git commit -m "fix(landing): address build/lint issues"
```

---

## Task 18: Final Review and Documentation

**Step 1: Verify all sections render**

Manually verify:
- [ ] Navigation appears and mobile menu works
- [ ] Hero section displays with gradient and CTAs
- [ ] Problem section shows contrast grid
- [ ] Capability cards have visible Three.js animations
- [ ] Audience tabs switch correctly
- [ ] Architecture diagram renders
- [ ] Footer links are correct

**Step 2: Create feature branch summary**

Run:
```bash
git log --oneline main..HEAD
```

Document the commits for PR description.

**Step 3: Push feature branch**

```bash
git push -u origin feature/landing-page
```

---

## Summary

This plan creates the complete landing page with:
- **6 main sections**: Hero, Problem, Capabilities, Audiences, Architecture, Footer
- **4 Three.js animations**: Ontology graph, Agent swarm, Code loop, Timeline compression
- **Responsive design**: Mobile-first with dark theme
- **Accessibility**: Reduced motion support
- **SEO**: Proper metadata and Open Graph tags

Total estimated tasks: 18
Files created: ~15 new components
Lines of code: ~1,500
