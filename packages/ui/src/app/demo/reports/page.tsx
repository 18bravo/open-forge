'use client';

import { BarChart3, FileText, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

/**
 * Demo reports page - placeholder showing what reports would look like
 */
export default function DemoReportsPage() {
  return (
    <div className="container py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
        <p className="text-muted-foreground">Analytics and insights from your engagements</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              Engagement Analytics
            </CardTitle>
            <CardDescription>Performance metrics across all engagements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">12</div>
            <p className="text-sm text-muted-foreground">Completed this month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              Data Processing
            </CardTitle>
            <CardDescription>Records processed and transformed</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">2.5M</div>
            <p className="text-sm text-muted-foreground">Records this month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-purple-500" />
              Agent Activity
            </CardTitle>
            <CardDescription>AI agent task completion rates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">94%</div>
            <p className="text-sm text-muted-foreground">Success rate</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Full Reporting Suite</CardTitle>
          <CardDescription>
            The complete platform includes advanced reporting features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li>Custom dashboards and visualizations</li>
            <li>Scheduled report generation</li>
            <li>Export to PDF, CSV, and Excel</li>
            <li>Real-time monitoring and alerts</li>
            <li>Historical trend analysis</li>
          </ul>
          <div className="pt-4">
            <Link href="/docs/quickstart">
              <Button>Get Started</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
