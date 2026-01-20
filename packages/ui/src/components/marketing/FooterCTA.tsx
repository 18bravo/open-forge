import Link from 'next/link';
import Image from 'next/image';
import { Github, BookOpen, Mail, ExternalLink } from 'lucide-react';

interface CtaCard {
  title: string;
  description: string;
  cta: string;
  href: string;
  icon: React.ElementType;
}

interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

const ctaCards: CtaCard[] = [
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

const footerLinks: Record<string, FooterLink[]> = {
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
      <section className="py-24" id="get-started">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-4xl font-bold bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent sm:text-5xl">
              The Forge Is Open
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Whether you're an engineer ready to build, a leader ready to deploy, or an
              executive ready to break free—the platform is here. Open source. Self-hosted. Autonomous.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3 mb-16">
            {ctaCards.map((card) => {
              const Icon = card.icon;
              const isExternal = card.href.startsWith('http');
              return (
                <a
                  key={card.title}
                  href={card.href}
                  target={isExternal ? '_blank' : undefined}
                  rel={isExternal ? 'noopener noreferrer' : undefined}
                  className="group rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50 hover:bg-zinc-900"
                >
                  <Icon className="mb-4 h-8 w-8 text-violet-500" />
                  <h3 className="mb-2 text-xl font-semibold text-zinc-50">{card.title}</h3>
                  <p className="mb-4 text-sm text-zinc-400">{card.description}</p>
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-violet-400 group-hover:text-violet-300">
                    {card.cta}
                    <ExternalLink className="h-3 w-3" />
                  </span>
                </a>
              );
            })}
          </div>
        </div>
      </section>

      <div className="border-t border-zinc-800">
        <div className="mx-auto max-w-5xl px-6 py-12">
          <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
            <div>
              <Link href="/" className="flex items-center gap-2 mb-4">
                <Image
                  src="/open_forge.png"
                  alt="Open Forge"
                  width={32}
                  height={32}
                  className="h-8 w-8"
                />
                <span className="text-xl font-bold text-zinc-50">Open Forge</span>
              </Link>
              <p className="text-sm text-zinc-500">
                The open source ontology platform.
              </p>
            </div>

            {Object.entries(footerLinks).map(([category, links]) => (
              <div key={category}>
                <h4 className="mb-4 text-sm font-semibold text-zinc-50">{category}</h4>
                <ul className="space-y-2">
                  {links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        target={link.external ? '_blank' : undefined}
                        rel={link.external ? 'noopener noreferrer' : undefined}
                        className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-12 pt-8 border-t border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-zinc-500">
              Part of the{' '}
              <a href="https://overlordai.ai" target="_blank" rel="noopener noreferrer" className="text-zinc-300 hover:text-zinc-50">
                OverlordAI
              </a>{' '}
              family:{' '}
              {siblingProducts.map((product, i) => (
                <span key={product.name}>
                  <a
                    href={product.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-zinc-50"
                  >
                    {product.name}
                  </a>
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
