'use client';

import * as React from 'react';
import { Key, Plus, Trash2, Copy } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  createdAt: string;
  lastUsed: string | null;
  scopes: string[];
}

const demoApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production API',
    prefix: 'sk_prod_****',
    createdAt: '2024-01-15',
    lastUsed: '2024-01-19',
    scopes: ['read', 'write'],
  },
  {
    id: '2',
    name: 'Development API',
    prefix: 'sk_dev_****',
    createdAt: '2024-01-10',
    lastUsed: '2024-01-18',
    scopes: ['read', 'write', 'admin'],
  },
  {
    id: '3',
    name: 'Read-only Integration',
    prefix: 'sk_ro_****',
    createdAt: '2024-01-05',
    lastUsed: null,
    scopes: ['read'],
  },
];

export default function DemoApiKeysSettingsPage() {
  const [keys] = React.useState<ApiKey[]>(demoApiKeys);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground">
            Manage API keys and access tokens
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create API Key
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Key className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Active API Keys</CardTitle>
              <CardDescription>
                Keys used for programmatic access to the API
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{key.name}</p>
                    <code className="rounded bg-muted px-2 py-0.5 text-sm">
                      {key.prefix}
                    </code>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Created: {key.createdAt}</span>
                    <span>
                      Last used: {key.lastUsed || 'Never'}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    {key.scopes.map((scope) => (
                      <Badge key={scope} variant="secondary" className="text-xs">
                        {scope}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon">
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Key Best Practices</CardTitle>
          <CardDescription>
            Keep your API keys secure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-4 space-y-2 text-sm text-muted-foreground">
            <li>Never share API keys in public repositories or client-side code</li>
            <li>Use environment variables to store API keys</li>
            <li>Rotate keys regularly and revoke unused keys</li>
            <li>Use the minimum required scopes for each key</li>
            <li>Monitor key usage and set up alerts for unusual activity</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
