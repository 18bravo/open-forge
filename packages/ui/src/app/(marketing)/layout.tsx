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
