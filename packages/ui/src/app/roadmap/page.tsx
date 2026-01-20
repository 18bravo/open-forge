import { CheckCircle2, Circle, Clock } from 'lucide-react';

const roadmapItems = [
  { quarter: 'Q1 2026', status: 'completed', items: ['Core ontology engine', 'Agent framework with LangGraph', '6 specialized agent clusters', 'FastAPI + GraphQL API layer', 'React UI portal'] },
  { quarter: 'Q2 2026', status: 'in-progress', items: ['MCP adapters for agent tools', 'LangSmith observability', 'Enhanced code generation', 'Kubernetes deployment', 'Documentation site'] },
  { quarter: 'Q3 2026', status: 'planned', items: ['Visual pipeline builder', 'Real-time collaboration', 'Enterprise SSO', 'Managed cloud offering', 'Plugin marketplace'] },
  { quarter: 'Q4 2026', status: 'planned', items: ['Multi-tenant support', 'Advanced analytics dashboard', 'Workflow templates library', 'Mobile companion app', 'AI-powered data quality'] },
];

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle2 className="h-5 w-5 text-green-500" />;
  if (status === 'in-progress') return <Clock className="h-5 w-5 text-yellow-500" />;
  return <Circle className="h-5 w-5 text-zinc-600" />;
}

export default function RoadmapPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">Roadmap</h1>
          <p className="text-lg text-zinc-400">See what we're building and what's coming next.</p>
        </div>

        <div className="space-y-8">
          {roadmapItems.map((quarter) => (
            <div key={quarter.quarter} className={`rounded-xl border p-6 ${quarter.status === 'in-progress' ? 'border-violet-500/50 bg-violet-500/5' : 'border-zinc-800 bg-zinc-900/50'}`}>
              <div className="flex items-center gap-3 mb-4">
                <StatusIcon status={quarter.status} />
                <h2 className="text-xl font-semibold text-zinc-50">{quarter.quarter}</h2>
                <span className={`rounded-full px-3 py-1 text-xs ${quarter.status === 'completed' ? 'bg-green-500/20 text-green-400' : quarter.status === 'in-progress' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-zinc-800 text-zinc-400'}`}>
                  {quarter.status === 'completed' ? 'Completed' : quarter.status === 'in-progress' ? 'In Progress' : 'Planned'}
                </span>
              </div>
              <ul className="grid gap-2 md:grid-cols-2">
                {quarter.items.map((item) => (
                  <li key={item} className="flex items-center gap-2 text-zinc-400">
                    <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-zinc-500">Want to influence the roadmap? <a href="https://github.com/overlordai/open-forge/discussions" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:text-violet-300">Join the discussion on GitHub</a></p>
        </div>
      </div>
    </div>
  );
}
