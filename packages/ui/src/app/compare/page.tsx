import { Check, X, Minus } from 'lucide-react';

const features = [
  { name: 'Open Source', openForge: true, palantir: false, snowflake: false },
  { name: 'Self-Hosted Option', openForge: true, palantir: false, snowflake: true },
  { name: 'Ontology Engine', openForge: true, palantir: true, snowflake: false },
  { name: 'AI Agents', openForge: true, palantir: 'partial', snowflake: 'partial' },
  { name: 'Code Generation', openForge: true, palantir: false, snowflake: false },
  { name: 'No Vendor Lock-in', openForge: true, palantir: false, snowflake: false },
  { name: 'Free Forever', openForge: true, palantir: false, snowflake: false },
];

function FeatureIcon({ value }: { value: boolean | string }) {
  if (value === true) return <Check className="h-5 w-5 text-green-500" />;
  if (value === false) return <X className="h-5 w-5 text-red-500" />;
  return <Minus className="h-5 w-5 text-yellow-500" />;
}

export default function ComparePage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">Compare Open Forge</h1>
          <p className="text-lg text-zinc-400">See how Open Forge stacks up against proprietary alternatives.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left py-4 px-4 text-zinc-400 font-medium">Feature</th>
                <th className="text-center py-4 px-4"><span className="text-violet-400 font-semibold">Open Forge</span></th>
                <th className="text-center py-4 px-4"><span className="text-zinc-400">Palantir Foundry</span></th>
                <th className="text-center py-4 px-4"><span className="text-zinc-400">Snowflake</span></th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.name} className="border-b border-zinc-800/50">
                  <td className="py-4 px-4 text-zinc-300">{feature.name}</td>
                  <td className="py-4 px-4 text-center"><div className="flex justify-center"><FeatureIcon value={feature.openForge} /></div></td>
                  <td className="py-4 px-4 text-center"><div className="flex justify-center"><FeatureIcon value={feature.palantir} /></div></td>
                  <td className="py-4 px-4 text-center"><div className="flex justify-center"><FeatureIcon value={feature.snowflake} /></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-12 rounded-xl border border-violet-500/30 bg-violet-500/10 p-6 text-center">
          <p className="text-zinc-300"><strong className="text-violet-400">The Bottom Line:</strong> Open Forge delivers enterprise-grade capabilities without the enterprise price tag.</p>
        </div>
      </div>
    </div>
  );
}
