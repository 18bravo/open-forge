import type { Metadata, Viewport } from 'next';
import { Inter as FontSans, JetBrains_Mono as FontMono } from 'next/font/google';

import { cn } from '@/lib/utils';
import { Providers } from '@/components/providers';

import './globals.css';

const fontSans = FontSans({
  subsets: ['latin'],
  variable: '--font-sans',
});

const fontMono = FontMono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: {
    default: 'Open Forge',
    template: '%s | Open Forge',
  },
  description: 'Open-source data platform for building and managing data-driven applications',
  keywords: [
    'data platform',
    'analytics',
    'data engineering',
    'open source',
    'foundry alternative',
  ],
  authors: [
    {
      name: 'Open Forge Team',
    },
  ],
  creator: 'Open Forge',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://openforge.dev',
    title: 'Open Forge',
    description: 'Open-source data platform for building and managing data-driven applications',
    siteName: 'Open Forge',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Open Forge',
    description: 'Open-source data platform for building and managing data-driven applications',
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
  width: 'device-width',
  initialScale: 1,
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body
        className={cn(
          'min-h-screen bg-background font-sans antialiased',
          fontSans.variable,
          fontMono.variable
        )}
      >
        <Providers>
          <div className="relative flex min-h-screen flex-col">
            <main className="flex-1">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
