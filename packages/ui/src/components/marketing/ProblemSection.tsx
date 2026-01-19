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
