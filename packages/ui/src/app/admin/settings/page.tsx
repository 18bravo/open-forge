'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  Bell,
  Database,
  Globe,
  Key,
  Loader2,
  Plug,
  Save,
  ScrollText,
  Server,
  Settings,
  Shield,
  Users,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useSystemSettings, useUpdateSettings } from '@/lib/hooks';

interface SettingSection {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  status?: 'configured' | 'warning' | 'error';
}

export default function SettingsPage() {
  const { data: apiSettings, isLoading, error } = useSystemSettings();
  const updateSettings = useUpdateSettings();

  // Local form state - initialized from API data
  const [formState, setFormState] = React.useState({
    instanceName: '',
    instanceUrl: '',
    adminEmail: '',
    sessionTimeoutMinutes: 60,
    requireMfa: false,
    allowSelfRegistration: false,
    defaultUserRole: 'viewer',
  });

  // Track if form has been modified
  const [isDirty, setIsDirty] = React.useState(false);

  // Update local state when API data loads
  React.useEffect(() => {
    if (apiSettings) {
      setFormState({
        instanceName: apiSettings.instance_name,
        instanceUrl: apiSettings.instance_url,
        adminEmail: apiSettings.admin_email,
        sessionTimeoutMinutes: apiSettings.session_timeout_minutes,
        requireMfa: apiSettings.require_mfa,
        allowSelfRegistration: apiSettings.allow_self_registration,
        defaultUserRole: apiSettings.default_user_role,
      });
    }
  }, [apiSettings]);

  const settingSections: SettingSection[] = [
    {
      title: 'Connectors',
      description: 'Configure data source and destination connectors',
      href: '/admin/settings/connectors',
      icon: Plug,
      status: 'configured',
    },
    {
      title: 'Users & Access',
      description: 'Manage users, roles, and permissions',
      href: '/admin/settings/users',
      icon: Users,
      status: 'configured',
    },
    {
      title: 'Audit Log',
      description: 'View system audit logs and activity history',
      href: '/admin/settings/audit',
      icon: ScrollText,
    },
    {
      title: 'Security',
      description: 'Authentication, encryption, and security policies',
      href: '/admin/settings/security',
      icon: Shield,
      status: 'warning',
    },
    {
      title: 'Notifications',
      description: 'Configure alerts, webhooks, and email settings',
      href: '/admin/settings/notifications',
      icon: Bell,
    },
    {
      title: 'API Keys',
      description: 'Manage API keys and access tokens',
      href: '/admin/settings/api-keys',
      icon: Key,
    },
  ];

  const handleSave = async () => {
    updateSettings.mutate({
      instance_name: formState.instanceName,
      instance_url: formState.instanceUrl,
      admin_email: formState.adminEmail,
      session_timeout_minutes: formState.sessionTimeoutMinutes,
      require_mfa: formState.requireMfa,
      allow_self_registration: formState.allowSelfRegistration,
      default_user_role: formState.defaultUserRole,
    }, {
      onSuccess: () => {
        setIsDirty(false);
      },
    });
  };

  const updateFormField = <K extends keyof typeof formState>(field: K, value: typeof formState[K]) => {
    setFormState(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'configured':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <p className="text-lg font-medium">Failed to load settings</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground">
            Configure and manage your Open Forge instance
          </p>
        </div>
        <Button onClick={handleSave} disabled={updateSettings.isPending || !isDirty}>
          {updateSettings.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          {updateSettings.isPending ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {updateSettings.isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to save settings: {updateSettings.error?.message}
          </p>
        </div>
      )}

      {/* Quick Navigation */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {settingSections.map((section) => (
          <Link key={section.href} href={section.href}>
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <section.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{section.title}</CardTitle>
                    </div>
                  </div>
                  {section.status && (
                    <div
                      className={cn(
                        'h-2 w-2 rounded-full',
                        getStatusColor(section.status)
                      )}
                      title={section.status}
                    />
                  )}
                </div>
                <CardDescription className="mt-2">
                  {section.description}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Settings className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>General Settings</CardTitle>
              <CardDescription>
                Basic configuration for your Open Forge instance
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="instanceName">Instance Name</Label>
              <Input
                id="instanceName"
                value={formState.instanceName}
                onChange={(e) => updateFormField('instanceName', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="instanceUrl">Instance URL</Label>
              <Input
                id="instanceUrl"
                value={formState.instanceUrl}
                onChange={(e) => updateFormField('instanceUrl', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="adminEmail">Admin Email</Label>
              <Input
                id="adminEmail"
                type="email"
                value={formState.adminEmail}
                onChange={(e) => updateFormField('adminEmail', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sessionTimeout">Session Timeout (minutes)</Label>
              <Input
                id="sessionTimeout"
                type="number"
                value={formState.sessionTimeoutMinutes}
                onChange={(e) => updateFormField('sessionTimeoutMinutes', parseInt(e.target.value) || 60)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>Security Settings</CardTitle>
              <CardDescription>
                Configure authentication and access controls
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">Require MFA</p>
              <p className="text-sm text-muted-foreground">
                Require multi-factor authentication for all users
              </p>
            </div>
            <button
              onClick={() => updateFormField('requireMfa', !formState.requireMfa)}
              className={cn(
                'relative h-6 w-11 rounded-full transition-colors',
                formState.requireMfa ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform',
                  formState.requireMfa && 'translate-x-5'
                )}
              />
            </button>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium">Allow Self Registration</p>
              <p className="text-sm text-muted-foreground">
                Allow users to register accounts without an invitation
              </p>
            </div>
            <button
              onClick={() => updateFormField('allowSelfRegistration', !formState.allowSelfRegistration)}
              className={cn(
                'relative h-6 w-11 rounded-full transition-colors',
                formState.allowSelfRegistration ? 'bg-primary' : 'bg-muted'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform',
                  formState.allowSelfRegistration && 'translate-x-5'
                )}
              />
            </button>
          </div>

          <div className="space-y-2">
            <Label htmlFor="defaultUserRole">Default User Role</Label>
            <select
              id="defaultUserRole"
              value={formState.defaultUserRole}
              onChange={(e) => updateFormField('defaultUserRole', e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="viewer">Viewer</option>
              <option value="editor">Editor</option>
              <option value="admin">Admin</option>
            </select>
            <p className="text-xs text-muted-foreground">
              The default role assigned to new users
            </p>
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>System Information</CardTitle>
              <CardDescription>
                Current system status and version information
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Version</p>
              <p className="text-lg font-semibold">v2.4.1</p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Environment</p>
              <p className="text-lg font-semibold">Production</p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Database</p>
              <p className="text-lg font-semibold">PostgreSQL 15</p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">Last Updated</p>
              <p className="text-lg font-semibold">Jan 10, 2024</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
