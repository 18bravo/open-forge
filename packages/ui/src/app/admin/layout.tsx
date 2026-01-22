'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Activity,
  AlertCircle,
  Bot,
  ChevronLeft,
  ChevronRight,
  Cog,
  Database,
  LayoutDashboard,
  ListTodo,
  LogOut,
  Plug,
  ScrollText,
  Settings,
  Users,
  Workflow,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  children?: NavItem[];
}

const navigation: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
  },
  {
    title: 'Agents',
    href: '/admin/agents',
    icon: Bot,
    children: [
      { title: 'All Agents', href: '/admin/agents', icon: Bot },
      { title: 'Discovery Cluster', href: '/admin/agents/discovery', icon: Database },
      { title: 'Data Architect', href: '/admin/agents/data-architect', icon: Workflow },
      { title: 'App Builder', href: '/admin/agents/app-builder', icon: Cog },
      { title: 'All Tasks', href: '/admin/agents/tasks', icon: ListTodo },
    ],
  },
  {
    title: 'Pipelines',
    href: '/admin/pipelines',
    icon: Workflow,
    children: [
      { title: 'All Pipelines', href: '/admin/pipelines', icon: Workflow },
      { title: 'Pipeline Runs', href: '/admin/pipelines/runs', icon: Activity },
    ],
  },
  {
    title: 'Settings',
    href: '/admin/settings',
    icon: Settings,
    children: [
      { title: 'General', href: '/admin/settings', icon: Settings },
      { title: 'Connectors', href: '/admin/settings/connectors', icon: Plug },
      { title: 'Users', href: '/admin/settings/users', icon: Users },
      { title: 'Audit Log', href: '/admin/settings/audit', icon: ScrollText },
    ],
  },
];

interface AdminLayoutProps {
  children: React.ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);
  const [expandedGroups, setExpandedGroups] = React.useState<string[]>(['Agents', 'Pipelines', 'Settings']);

  // Role-based access check - in production this would check actual user roles
  const [hasAccess, setHasAccess] = React.useState<boolean | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    // Simulate role check - in production, fetch from auth context or API
    const checkAccess = async () => {
      try {
        // This would typically check against your auth system
        // For now, we'll simulate admin access
        const isAdmin = true; // Replace with actual role check
        setHasAccess(isAdmin);
      } catch {
        setHasAccess(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAccess();
  }, []);

  const toggleGroup = (title: string) => {
    setExpandedGroups((prev) =>
      prev.includes(title) ? prev.filter((g) => g !== title) : [...prev, title]
    );
  };

  const isActive = (href: string) => {
    if (href === '/admin') {
      return pathname === '/admin';
    }
    return pathname.startsWith(href);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!hasAccess) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <AlertCircle className="h-16 w-16 text-destructive" />
        <h1 className="text-2xl font-bold">Access Denied</h1>
        <p className="text-muted-foreground">
          You do not have permission to access the admin dashboard.
        </p>
        <Button asChild>
          <Link href="/">Return Home</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside
        className={cn(
          'sticky top-0 flex h-screen flex-col border-r bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Sidebar Header */}
        <div className="flex h-14 items-center border-b px-4">
          {!collapsed && (
            <Link href="/admin" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold">
                OF
              </div>
              <span className="font-semibold">Admin</span>
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
                {item.children ? (
                  <div>
                    <button
                      onClick={() => toggleGroup(item.title)}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                        isActive(item.href) && 'bg-accent text-accent-foreground'
                      )}
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      {!collapsed && (
                        <>
                          <span className="flex-1 text-left">{item.title}</span>
                          <ChevronRight
                            className={cn(
                              'h-4 w-4 transition-transform',
                              expandedGroups.includes(item.title) && 'rotate-90'
                            )}
                          />
                        </>
                      )}
                    </button>
                    {!collapsed && expandedGroups.includes(item.title) && (
                      <ul className="ml-4 mt-1 space-y-1 border-l pl-4">
                        {item.children.map((child) => (
                          <li key={child.href}>
                            <Link
                              href={child.href}
                              className={cn(
                                'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground',
                                isActive(child.href) &&
                                  pathname === child.href &&
                                  'bg-accent text-accent-foreground font-medium'
                              )}
                            >
                              <child.icon className="h-4 w-4 shrink-0" />
                              <span>{child.title}</span>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : (
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
                )}
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
            {!collapsed && <span>Exit Admin</span>}
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="container py-6">{children}</div>
      </main>
    </div>
  );
}
