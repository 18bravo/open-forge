# Open Forge Landing Page Design

**Date:** 2026-01-19
**Status:** Approved
**Domain:** forge.overlordai.ai

---

## Overview

Landing page for Open Forge, positioned as the open-source alternative to Palantir's enterprise data platform. The page targets three audiences with distinct value propositions while maintaining a cohesive anti-vendor-lock-in narrative.

### Target Audiences

1. **Software Engineers** — Contributors seeking a righteous open-source project
2. **Technical Leaders** — Business leadership wanting control over their data platform
3. **Executives** — Decision-makers seeking AI enablement without vendor lock-in

### Brand Alignment

Part of the OverlordAI ecosystem alongside:
- app.overlordai.ai (Overlord AI) — AI workforce creation
- wisdom.overlordai.ai (OrgWisdom) — Collective wisdom/feedback
- anthill.overlordai.ai (Anthill AI) — 2.5D virtual workspace

**Visual Theme:** Dark mode, violet/purple gradients, modern tech aesthetic

---

## Section 1: Hero

### Headline
> **The Open Source Ontology Platform**

### Subheadline
> Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in. Your ontology, your operations, your code.

### Supporting Text
> Why pay millions for proprietary platforms and forward-deployed engineers when autonomous agents can build, integrate, and operate your data infrastructure 24/7?

### CTAs (Three-Column)

| For Engineers | For Leaders | For Executives |
|---------------|-------------|----------------|
| Star on GitHub | Deploy Now | Request Demo |

### Visual Elements
- Dark mode with violet/purple gradient accents
- Animated visualization showing agents autonomously building data pipelines
- No human consultants depicted

### Social Proof Strip
> "20+ Autonomous Agents | 6 Agent Clusters | Full Stack Code Generation | Apache 2.0 Licensed"

---

## Section 2: The Problem (Anti-FDE Manifesto)

### Headline
> **The $10M Question**

### Body Copy
> Enterprise data platforms promised transformation. They delivered dependency.

> You wanted an operating system for your business. You got a consulting engagement that never ends. You wanted to run your business as code. You got a team of forward-deployed engineers running it for you—at $500K per head, per year.

> The dirty secret? The "ontology" they sold you—the semantic layer connecting your data to decisions—isn't magic. It's engineering. Engineering that autonomous AI agents can now perform faster, cheaper, and without the billable hours.

### Contrast Grid

| The Old Way | | The Open Way |
|-------------|---|--------------|
| Proprietary ontology platform | → | Open source ontology engine |
| Forward-deployed engineers | → | Autonomous agent clusters |
| Years to value | → | Days to deployment |
| Vendor lock-in | → | Apache 2.0 licensed |
| Black box operations | → | Transparent, auditable code |
| $10M+ annual contracts | → | Self-hosted, free forever |

### Closing Line
> The era of indentured data platforms is over.

---

## Section 3: Platform Capabilities

### Section Headline
> **Ontology-Powered. Agent-Operated.**

### Section Subhead
> Everything they promised. Nothing they control.

### Capability Cards with Three.js Animations

Each card features a subtle, looping Three.js animation as background—dark with violet/purple accents.

---

#### Card 1: The Ontology Engine

**Copy:**
> Define the semantic, kinetic, and dynamic elements of your business—objects, actions, relationships—in an open schema language. Your ontology compiles to SQL, GraphQL, Pydantic, TypeScript, and Cypher. No proprietary formats. No lock-in.

**Three.js Animation:**
A dynamic 3D knowledge graph that continuously forms and reforms. Nodes (representing entities like "Customer", "Order", "Product") float in space and connect with glowing edges. Periodically, the graph "compiles"—nodes pulse and transform into different shapes representing output formats (database table icon, GraphQL logo, TypeScript brackets). The transformation ripples outward like a shockwave.

**Interaction:** On hover, graph rotation speeds up and nodes highlight on mouseover.

---

#### Card 2: Autonomous Agent Clusters

**Copy:**
> Six specialized clusters—Discovery, Data Architect, App Builder, Operations, Enablement, and Orchestration—coordinate to analyze, design, build, and operate your data infrastructure. 20+ agents working in parallel, 24/7.

**Three.js Animation:**
A 3D hive/swarm visualization. Twenty+ small glowing orbs (agents) organized into 6 distinct cluster formations, each cluster a different shade of violet/cyan. Agents pulse with activity, occasionally sending particle trails to other clusters showing inter-cluster communication. The whole system breathes—expanding and contracting rhythmically to suggest autonomous coordination.

**Interaction:** On hover, agents move faster and communication trails intensify.

---

#### Card 3: Closed-Loop Code Generation

**Copy:**
> From ontology to production in one workflow. Generate FastAPI routes, SQLAlchemy models, React components, test suites, and infrastructure configs. Agents validate, refine, and deploy—no consultants in the loop.

**Three.js Animation:**
An infinite loop visualization—a 3D Möbius strip or circular pipeline. Code snippets (syntax-highlighted fragments) flow along the loop, entering as "schema definitions" on one side and emerging as "generated code" (Python, TypeScript, SQL) on the other. At the validation checkpoint, some fragments glow green (pass) while occasional ones loop back for refinement (glow amber, re-enter the cycle).

**Interaction:** On hover, flow speed increases and code fragments become more legible.

---

#### Card 4: Day 1 Value

**Copy:**
> Deploy on your infrastructure today. Connect your data sources. Watch agents discover schemas, design transformations, and generate working applications. Days, not years.

**Three.js Animation:**
A deployment timeline that compresses dramatically. Starts with a 3D calendar/timeline showing "Year 1... Year 2... Year 3..." which then rapidly collapses and crunches down into "Day 1" with a satisfying impact effect. Infrastructure icons (servers, databases, containers) spin up and connect in rapid succession. A progress ring fills instantly. Repeats on loop.

**Interaction:** On hover, the compression effect replays with more dramatic particle effects.

---

### Technical Requirements for Animations

- Use `react-three-fiber` for React integration
- Keep polygon counts low for performance
- Animations should be subtle enough not to distract from copy
- Reduce motion for `prefers-reduced-motion` accessibility
- Dark background (`zinc-900`) with `violet-500`/`purple-500` accent glows

---

## Section 4: Audience Segments

### Section Headline
> **Built For Everyone Who's Had Enough**

Implemented as three tabbed sections or stacked sections.

---

### Tab A: For Engineers

**Headline:**
> **Own the Code That Runs the World**

**Body:**
> The platforms that power Fortune 500 data operations shouldn't be proprietary black boxes. Open Forge is the ontology platform built in the open—Python, TypeScript, LangGraph, FastAPI, React—modern stack, MIT-educated architecture, Apache 2.0 licensed.

> This isn't a toy. It's 80,000+ lines of production code across 10 packages: ontology compilers, connector frameworks, pipeline engines, agent orchestration, human-in-the-loop workflows, and full-stack code generation.

> The proprietary platforms had a 20-year head start. We have a community.

**CTAs:** `Star on GitHub` | `Read the Architecture` | `First Good Issues`

---

### Tab B: For Technical Leaders

**Headline:**
> **Your Data Platform. Your Rules.**

**Body:**
> Stop renting your data infrastructure. Open Forge deploys on your cloud, your Kubernetes cluster, your terms. Connect to PostgreSQL, MySQL, S3, REST APIs, GraphQL endpoints—50+ connector types with schema discovery built in.

> The ontology layer you define is portable. The pipelines are Dagster-native. The APIs are standard REST and GraphQL. When you need to change direction, you change direction—no exit negotiations, no migration fees, no hostage situations.

**CTAs:** `Deploy on Your Infrastructure` | `View Connectors` | `Book Architecture Review`

---

### Tab C: For Executives

**Headline:**
> **AI Transformation Without the Tribute**

**Body:**
> Your competitors are spending $10M+ annually on proprietary platforms and armies of consultants. You can deploy the same ontology-powered, AI-operated infrastructure—and own it outright.

> Open Forge's autonomous agents replace the forward-deployed engineer model entirely. Discovery agents interview stakeholders. Architect agents design schemas. Builder agents generate applications. Operations agents monitor and scale. 24/7, no billable hours.

> This is AI enablement without indentured servitude.

**CTAs:** `Request Executive Briefing` | `View ROI Calculator` | `Compare to Alternatives`

---

## Section 5: Technical Credibility

### Section Headline
> **Full Stack. Open Source. Production Ready.**

### Architecture Diagram

Interactive Three.js visualization showing the platform layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      UI Portal (React/Next.js)              │
├─────────────────────────────────────────────────────────────┤
│            API Gateway (FastAPI + GraphQL + SSE)            │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Discovery  │    Data      │  App Builder │   Operations   │
│    Agents    │  Architect   │    Agents    │    Agents      │
│              │   Agents     │              │                │
├──────────────┴──────────────┴──────────────┴────────────────┤
│              Agent Framework (LangGraph)                    │
├─────────────────────────────────────────────────────────────┤
│   Ontology Engine  │  Codegen Engine  │  Pipeline Engine   │
├─────────────────────────────────────────────────────────────┤
│         Connectors (PostgreSQL, S3, REST, GraphQL...)       │
└─────────────────────────────────────────────────────────────┘
```

**Animation:** The diagram is 3D with depth. Data flows visibly between layers as glowing particles. Clicking a layer expands it to show subcomponents.

### Stats Strip

| 10 Packages | 20+ Agents | 50+ API Endpoints | 7 Connectors | 4 Code Generators |
|-------------|------------|-------------------|--------------|-------------------|

**Link:** `Explore the Full Architecture →`

---

## Section 6: Final CTA / Footer

### Section Headline
> **The Forge Is Open**

### Final Pitch
> Whether you're an engineer ready to build, a leader ready to deploy, or an executive ready to break free—the platform is here. Open source. Self-hosted. Autonomous.

### CTA Cards (Three Columns)

| **Contribute** | **Deploy** | **Connect** |
|----------------|------------|-------------|
| Join engineers building the open alternative | Get running on your infrastructure today | Talk to our team about your use case |
| `Star on GitHub` | `Quick Start Guide` | `Request Demo` |

### Footer Links

**Product:**
- Documentation
- Architecture Docs
- Quick Start Guide
- Roadmap

**Community:**
- GitHub
- Discord
- Twitter/X
- Blog

**Company:**
- About OverlordAI
- Contact
- Careers

### Brand Footer
> Part of the **OverlordAI** family: [Overlord](https://app.overlordai.ai) · [Wisdom](https://wisdom.overlordai.ai) · [Anthill](https://anthill.overlordai.ai) · **Forge**

---

## Technical Implementation Notes

### Stack
- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS with custom violet/purple theme
- **3D:** Three.js via react-three-fiber
- **Animations:** Framer Motion for transitions, Three.js for background animations
- **Icons:** Lucide React

### Performance Considerations
- Lazy load Three.js components
- Use Intersection Observer to pause off-screen animations
- Implement `prefers-reduced-motion` media query support
- SSG for core content, client-side hydration for interactive elements

### SEO
- Meta title: "Open Forge | The Open Source Ontology Platform"
- Meta description: "Enterprise-grade data infrastructure with autonomous AI agents. No consultants required. No vendor lock-in. Apache 2.0 licensed."
- Open Graph images for each audience segment

### Analytics Events
- CTA clicks (segmented by audience type)
- Tab switches in audience section
- Architecture diagram interactions
- Scroll depth tracking
- GitHub star click attribution

---

## File Structure

```
packages/ui/src/app/(marketing)/
├── page.tsx                    # Landing page
├── components/
│   ├── Hero.tsx
│   ├── ProblemSection.tsx
│   ├── CapabilityCards/
│   │   ├── index.tsx
│   │   ├── OntologyAnimation.tsx
│   │   ├── AgentSwarmAnimation.tsx
│   │   ├── CodeLoopAnimation.tsx
│   │   └── TimelineAnimation.tsx
│   ├── AudienceSegments.tsx
│   ├── ArchitectureDiagram.tsx
│   └── FooterCTA.tsx
```

---

## Next Steps

1. Set up marketing route group in existing Next.js app
2. Implement hero section with static content
3. Build Three.js animation components (can be parallelized)
4. Implement audience segment tabs
5. Create interactive architecture diagram
6. Add analytics tracking
7. SEO optimization and meta tags
8. Performance testing and optimization
