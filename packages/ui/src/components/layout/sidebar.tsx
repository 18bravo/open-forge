'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Briefcase,
  Bot,
  BarChart3,
  Settings,
  Users,
  Database,
  FileText,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface SidebarProps {
  className?: string;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const mainNavItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Engagements',
    href: '/engagements',
    icon: Briefcase,
  },
  {
    title: 'Agents',
    href: '/agents',
    icon: Bot,
  },
  {
    title: 'Analytics',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    title: 'Data Sources',
    href: '/data-sources',
    icon: Database,
  },
  {
    title: 'Reports',
    href: '/reports',
    icon: FileText,
  },
];

const secondaryNavItems: NavItem[] = [
  {
    title: 'Team',
    href: '/team',
    icon: Users,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar({ className, isOpen = true, onOpenChange }: SidebarProps) {
  const pathname = usePathname();

  const NavLink = ({ item, collapsed }: { item: NavItem; collapsed: boolean }) => {
    const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
    const Icon = item.icon;

    const linkContent = (
      <Link
        href={item.href}
        className={cn(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
          collapsed && 'justify-center px-2'
        )}
      >
        <Icon className="h-4 w-4 shrink-0" />
        {!collapsed && <span>{item.title}</span>}
        {!collapsed && item.badge && (
          <span className="ml-auto rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            {item.badge}
          </span>
        )}
      </Link>
    );

    if (collapsed) {
      return (
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
          <TooltipContent side="right" className="flex items-center gap-4">
            {item.title}
            {item.badge && (
              <span className="ml-auto text-muted-foreground">{item.badge}</span>
            )}
          </TooltipContent>
        </Tooltip>
      );
    }

    return linkContent;
  };

  return (
    <TooltipProvider>
      <aside
        className={cn(
          'relative flex flex-col border-r bg-background transition-all duration-300',
          isOpen ? 'w-64' : 'w-16',
          className
        )}
      >
        <div className="flex flex-1 flex-col gap-2 p-4">
          <nav className="flex flex-col gap-1">
            {mainNavItems.map((item) => (
              <NavLink key={item.href} item={item} collapsed={!isOpen} />
            ))}
          </nav>

          <Separator className="my-2" />

          <nav className="flex flex-col gap-1">
            {secondaryNavItems.map((item) => (
              <NavLink key={item.href} item={item} collapsed={!isOpen} />
            ))}
          </nav>
        </div>

        <div className="border-t p-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-center"
            onClick={() => onOpenChange?.(!isOpen)}
          >
            {isOpen ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <span className="sr-only">
              {isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            </span>
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
