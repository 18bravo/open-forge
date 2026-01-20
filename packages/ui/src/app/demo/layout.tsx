'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  Bot,
  ChevronLeft,
  ChevronRight,
  CheckSquare,
  Database,
  Home,
  LayoutDashboard,
  LogOut,
  Settings,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { setGlobalDemoMode } from '@/lib/demo-context';
import { DemoBanner } from '@/components/demo-banner';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navigation: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/demo/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Engagements',
    href: '/demo/engagements',
    icon: Activity,
  },
  {
    title: 'Data Sources',
    href: '/demo/data-sources',
    icon: Database,
  },
  {
    title: 'Approvals',
    href: '/demo/approvals',
    icon: CheckSquare,
  },
  {
    title: 'Admin',
    href: '/demo/admin',
    icon: Settings,
  },
];

interface DemoLayoutProps {
  children: React.ReactNode;
}

export default function DemoLayout({ children }: DemoLayoutProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  // Enable demo mode when this layout mounts
  React.useEffect(() => {
    setGlobalDemoMode(true);
    return () => {
      setGlobalDemoMode(false);
    };
  }, []);

  const isActive = (href: string) => {
    if (href === '/demo/dashboard') {
      return pathname === '/demo/dashboard';
    }
    return pathname.startsWith(href);
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* Demo Banner */}
      <DemoBanner />

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside
          className={cn(
            'sticky top-0 flex h-[calc(100vh-40px)] flex-col border-r bg-card transition-all duration-300',
            collapsed ? 'w-16' : 'w-64'
          )}
        >
          {/* Sidebar Header */}
          <div className="flex h-14 items-center border-b px-4">
            {!collapsed && (
              <Link href="/demo/dashboard" className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold">
                  OF
                </div>
                <span className="font-semibold">Demo</span>
              </Link>
            )}
            <Button
              variant="ghost"
              size="icon"
              className={cn('ml-auto', collapsed && 'mx-auto')}
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-2">
            <ul className="space-y-1">
              {navigation.map((item) => (
                <li key={item.title}>
                  <Link
                    href={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                      isActive(item.href) && 'bg-accent text-accent-foreground'
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span>{item.title}</span>}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Sidebar Footer */}
          <div className="border-t p-2">
            <Link
              href="/"
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground',
                collapsed && 'justify-center'
              )}
            >
              <LogOut className="h-4 w-4 shrink-0" />
              {!collapsed && <span>Exit Demo</span>}
            </Link>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
