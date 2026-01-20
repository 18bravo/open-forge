'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { Menu, X, Github, Play } from 'lucide-react';

interface NavLink {
  href: string;
  label: string;
  external?: boolean;
}

const navLinks: NavLink[] = [
  { href: '#features', label: 'Features' },
  { href: '#architecture', label: 'Architecture' },
  { href: 'https://github.com/overlordai/open-forge', label: 'GitHub', external: true },
  { href: '/docs', label: 'Docs' },
];

function NavLinkItem({ link, className, onClick }: { link: NavLink; className?: string; onClick?: () => void }) {
  if (link.external || link.href.startsWith('#')) {
    return (
      <a
        href={link.href}
        target={link.external ? '_blank' : undefined}
        rel={link.external ? 'noopener noreferrer' : undefined}
        className={className}
        onClick={onClick}
      >
        {link.label}
      </a>
    );
  }
  return (
    <Link href={link.href as '/'} className={className} onClick={onClick}>
      {link.label}
    </Link>
  );
}

export function MarketingNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <Image
            src="/open_forge.png"
            alt="Open Forge"
            width={32}
            height={32}
            className="h-8 w-8"
          />
          <span className="text-xl font-bold">Open Forge</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <NavLinkItem
              key={link.href}
              link={link}
              className="text-sm text-zinc-400 hover:text-zinc-50 transition-colors"
            />
          ))}
          <a
            href="https://github.com/overlordai/open-forge"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium hover:bg-zinc-700 transition-colors"
          >
            <Github className="h-4 w-4" />
            Star on GitHub
          </a>
          <Link
            href="/demo/dashboard"
            className="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
          >
            <Play className="h-4 w-4" />
            Launch Demo
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-zinc-800 bg-zinc-950 px-6 py-4">
          {navLinks.map((link) => (
            <NavLinkItem
              key={link.href}
              link={link}
              className="block py-3 text-zinc-400 hover:text-zinc-50"
              onClick={() => setMobileMenuOpen(false)}
            />
          ))}
          <Link
            href="/demo/dashboard"
            className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-3 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
            onClick={() => setMobileMenuOpen(false)}
          >
            <Play className="h-4 w-4" />
            Launch Demo
          </Link>
        </div>
      )}
    </header>
  );
}
