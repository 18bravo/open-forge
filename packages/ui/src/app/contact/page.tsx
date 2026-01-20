'use client';

import { Mail, MessageSquare } from 'lucide-react';

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-2xl px-6">
        <div className="text-center mb-12">
          <Mail className="h-12 w-12 text-violet-500 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-zinc-50 mb-4">Contact Us</h1>
          <p className="text-lg text-zinc-400">Have questions? We'd love to hear from you.</p>
        </div>

        <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Name</label>
              <input type="text" className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-zinc-50 focus:border-violet-500 focus:outline-none" placeholder="Your name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Email</label>
              <input type="email" className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-zinc-50 focus:border-violet-500 focus:outline-none" placeholder="you@company.com" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Company</label>
            <input type="text" className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-zinc-50 focus:border-violet-500 focus:outline-none" placeholder="Your company" />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Message</label>
            <textarea rows={5} className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-zinc-50 focus:border-violet-500 focus:outline-none resize-none" placeholder="Tell us about your use case..." />
          </div>

          <button type="submit" className="w-full rounded-lg bg-violet-600 px-6 py-3 font-semibold text-white hover:bg-violet-500 transition-colors">Send Message</button>
        </form>

        <div className="mt-12 grid gap-4 md:grid-cols-2">
          <a href="mailto:hello@overlordai.ai" className="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-violet-500/50">
            <Mail className="h-5 w-5 text-violet-500" />
            <span className="text-zinc-300">hello@overlordai.ai</span>
          </a>
          <a href="https://discord.gg/overlordai" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-violet-500/50">
            <MessageSquare className="h-5 w-5 text-violet-500" />
            <span className="text-zinc-300">Join our Discord</span>
          </a>
        </div>
      </div>
    </div>
  );
}
