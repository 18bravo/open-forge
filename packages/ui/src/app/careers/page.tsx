import { Briefcase, MapPin, Clock, ArrowRight } from 'lucide-react';

const positions = [
  { title: 'Senior Full-Stack Engineer', location: 'Remote', type: 'Full-time', description: 'Help build the open-source ontology platform that's changing how enterprises work with data.' },
  { title: 'AI/ML Engineer', location: 'Remote', type: 'Full-time', description: 'Design and implement autonomous agents that replace traditional consulting models.' },
  { title: 'Developer Advocate', location: 'Remote', type: 'Full-time', description: 'Build and nurture the Open Forge community through content, events, and support.' },
];

export default function CareersPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-12">
          <Briefcase className="h-12 w-12 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">Join the Forge</h1>
          <p className="text-lg text-zinc-400">Help us build the future of open-source data infrastructure.</p>
        </div>

        <div className="mb-12 rounded-xl border border-violet-500/30 bg-violet-500/10 p-8">
          <h2 className="text-2xl font-semibold text-zinc-50 mb-4">Why Work With Us?</h2>
          <ul className="space-y-3 text-zinc-300">
            <li className="flex items-start gap-3"><div className="h-1.5 w-1.5 rounded-full bg-violet-500 mt-2" />Work on genuinely impactful open-source software</li>
            <li className="flex items-start gap-3"><div className="h-1.5 w-1.5 rounded-full bg-violet-500 mt-2" />Fully remote, async-first culture</li>
            <li className="flex items-start gap-3"><div className="h-1.5 w-1.5 rounded-full bg-violet-500 mt-2" />Competitive compensation + equity</li>
            <li className="flex items-start gap-3"><div className="h-1.5 w-1.5 rounded-full bg-violet-500 mt-2" />Work with cutting-edge AI/ML and data technologies</li>
          </ul>
        </div>

        <h2 className="text-2xl font-semibold text-zinc-50 mb-6">Open Positions</h2>

        <div className="space-y-4">
          {positions.map((position) => (
            <div key={position.title} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50">
              <h3 className="text-xl font-semibold text-zinc-50 mb-2">{position.title}</h3>
              <div className="flex items-center gap-4 mb-3 text-sm text-zinc-400">
                <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {position.location}</span>
                <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> {position.type}</span>
              </div>
              <p className="text-zinc-400 mb-4">{position.description}</p>
              <a href={`mailto:careers@overlordai.ai?subject=Application: ${position.title}`} className="inline-flex items-center gap-1 text-sm text-violet-400 hover:text-violet-300">Apply now <ArrowRight className="h-4 w-4" /></a>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center text-zinc-500">
          <p>Don't see a fit? Send us your resume at <a href="mailto:careers@overlordai.ai" className="text-violet-400 hover:text-violet-300">careers@overlordai.ai</a></p>
        </div>
      </div>
    </div>
  );
}
