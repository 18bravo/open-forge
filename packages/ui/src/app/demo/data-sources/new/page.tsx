'use client';

import { ArrowLeft, Database, Plus } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

/**
 * Demo version of the new data source page
 * Shows a placeholder since creating data sources doesn't make sense in demo mode
 */
export default function DemoNewDataSourcePage() {
  return (
    <div className="container py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/demo/data-sources">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add Data Source</h1>
          <p className="text-muted-foreground">Connect a new data source to Open Forge</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Demo Mode
          </CardTitle>
          <CardDescription>
            Data source creation is disabled in demo mode
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            In the full platform, you would be able to connect various data sources including:
          </p>
          <ul className="list-disc list-inside space-y-2 text-muted-foreground">
            <li>PostgreSQL, MySQL, and other relational databases</li>
            <li>Snowflake, BigQuery, and data warehouses</li>
            <li>S3, GCS, and cloud storage</li>
            <li>REST APIs and webhooks</li>
            <li>Kafka and message queues</li>
          </ul>
          <div className="pt-4">
            <Link href="/docs/quickstart">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Get Started with Real Data
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
