'use client';

import * as React from 'react';
import { Bell, Mail, MessageSquare, Webhook } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function DemoNotificationsSettingsPage() {
  const [settings, setSettings] = React.useState({
    emailNotifications: true,
    slackIntegration: false,
    webhookEnabled: true,
    webhookUrl: 'https://hooks.example.com/notify',
    digestFrequency: 'daily',
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Notification Settings</h1>
        <p className="text-muted-foreground">
          Configure alerts, webhooks, and email settings
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>
                Configure email alerts for system events
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Email Notifications</Label>
              <p className="text-sm text-muted-foreground">
                Send email alerts for important events
              </p>
            </div>
            <Switch
              checked={settings.emailNotifications}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, emailNotifications: checked })
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Digest Frequency</Label>
            <select
              value={settings.digestFrequency}
              onChange={(e) =>
                setSettings({ ...settings, digestFrequency: e.target.value })
              }
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="realtime">Real-time</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <MessageSquare className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Slack Integration</CardTitle>
              <CardDescription>
                Send notifications to Slack channels
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Slack Integration</Label>
              <p className="text-sm text-muted-foreground">
                Post updates to configured Slack channels
              </p>
            </div>
            <Switch
              checked={settings.slackIntegration}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, slackIntegration: checked })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Webhook className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Webhooks</CardTitle>
              <CardDescription>
                Send event data to external services
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Webhooks</Label>
              <p className="text-sm text-muted-foreground">
                Send HTTP POST requests on events
              </p>
            </div>
            <Switch
              checked={settings.webhookEnabled}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, webhookEnabled: checked })
              }
            />
          </div>

          {settings.webhookEnabled && (
            <div className="space-y-2">
              <Label>Webhook URL</Label>
              <Input
                value={settings.webhookUrl}
                onChange={(e) =>
                  setSettings({ ...settings, webhookUrl: e.target.value })
                }
                placeholder="https://your-webhook-url.com"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button>Save Changes</Button>
      </div>
    </div>
  );
}
