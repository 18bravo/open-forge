'use client';

import * as React from 'react';
import { Shield, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';

export default function DemoSecuritySettingsPage() {
  const [settings, setSettings] = React.useState({
    requireMfa: true,
    enforcePasswordPolicy: true,
    sessionTimeout: 60,
    ipWhitelist: false,
    auditLogging: true,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Security Settings</h1>
        <p className="text-muted-foreground">
          Configure authentication and security policies
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Authentication</CardTitle>
              <CardDescription>
                Configure how users authenticate with the system
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Require MFA</Label>
              <p className="text-sm text-muted-foreground">
                Require multi-factor authentication for all users
              </p>
            </div>
            <Switch
              checked={settings.requireMfa}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, requireMfa: checked })
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enforce Password Policy</Label>
              <p className="text-sm text-muted-foreground">
                Require strong passwords with minimum length and complexity
              </p>
            </div>
            <Switch
              checked={settings.enforcePasswordPolicy}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, enforcePasswordPolicy: checked })
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>IP Whitelist</Label>
              <p className="text-sm text-muted-foreground">
                Only allow access from approved IP addresses
              </p>
            </div>
            <Switch
              checked={settings.ipWhitelist}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, ipWhitelist: checked })
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Audit Logging</Label>
              <p className="text-sm text-muted-foreground">
                Log all user actions for compliance
              </p>
            </div>
            <Switch
              checked={settings.auditLogging}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, auditLogging: checked })
              }
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button>Save Changes</Button>
      </div>
    </div>
  );
}
