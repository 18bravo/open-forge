import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function HomePage() {
  return (
    <div className="container-wrapper">
      <section className="page-header">
        <h1 className="page-header-heading text-balance">
          <span className="gradient-text">Open Forge</span>
        </h1>
        <p className="page-header-description text-balance">
          The open-source data platform for building and managing data-driven applications.
          A powerful alternative for modern data teams.
        </p>
        <div className="flex gap-4">
          <Button asChild size="lg">
            <Link href="/dashboard">Get Started</Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/docs">Documentation</Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 py-12">
        <Card>
          <CardHeader>
            <CardTitle>Engagements</CardTitle>
            <CardDescription>
              Manage client engagements and projects with full lifecycle tracking.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Create, monitor, and analyze engagements across your organization.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>AI Agents</CardTitle>
            <CardDescription>
              Deploy intelligent agents to automate data workflows.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Configure and monitor AI-powered automation tasks.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analytics</CardTitle>
            <CardDescription>
              Powerful analytics and visualization tools.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Build dashboards and reports with integrated data sources.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
