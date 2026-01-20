import { BookOpen, ArrowRight } from 'lucide-react';

const posts = [
  { title: 'Introducing Open Forge: The Open Source Ontology Platform', excerpt: 'Today we're launching Open Forge, an open-source alternative to proprietary data platforms...', date: 'January 2026', category: 'Announcement' },
  { title: 'How Autonomous Agents Replace Forward-Deployed Engineers', excerpt: 'The traditional consulting model is broken. Here's how AI agents are changing the game...', date: 'Coming Soon', category: 'Technical' },
  { title: 'Building Your First Ontology with Open Forge', excerpt: 'A step-by-step guide to defining semantic, kinetic, and dynamic elements...', date: 'Coming Soon', category: 'Tutorial' },
];

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-12">
          <BookOpen className="h-12 w-12 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">Blog</h1>
          <p className="text-lg text-zinc-400">Insights, tutorials, and updates from the Open Forge team.</p>
        </div>

        <div className="space-y-6">
          {posts.map((post, i) => (
            <article key={post.title} className={`rounded-xl border p-6 transition-all hover:border-violet-500/50 ${i === 0 ? 'border-violet-500/30 bg-violet-500/5' : 'border-zinc-800 bg-zinc-900/50'}`}>
              <div className="flex items-center gap-3 mb-3">
                <span className="rounded-full bg-violet-500/20 px-3 py-1 text-xs text-violet-400">{post.category}</span>
                <span className="text-sm text-zinc-500">{post.date}</span>
              </div>
              <h2 className="text-xl font-semibold text-zinc-50 mb-2">{post.title}</h2>
              <p className="text-zinc-400 mb-4">{post.excerpt}</p>
              {i === 0 ? (
                <span className="inline-flex items-center gap-1 text-sm text-violet-400 hover:text-violet-300 cursor-pointer">Read more <ArrowRight className="h-4 w-4" /></span>
              ) : (
                <span className="text-sm text-zinc-600">Coming soon...</span>
              )}
            </article>
          ))}
        </div>

        <div className="mt-12 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 text-center">
          <p className="text-zinc-400 mb-4">Want to write for the Open Forge blog?</p>
          <a href="mailto:blog@overlordai.ai" className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300">Get in touch <ArrowRight className="h-4 w-4" /></a>
        </div>
      </div>
    </div>
  );
}
