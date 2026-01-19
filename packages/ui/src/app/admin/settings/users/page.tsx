'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  ArrowLeft,
  Edit,
  Key,
  Loader2,
  Mail,
  MoreVertical,
  Plus,
  RefreshCw,
  Search,
  Shield,
  ShieldCheck,
  Trash2,
  User,
  UserCheck,
  UserX,
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
import { useUsers } from '@/lib/hooks';
import type { UserSummary } from '@/lib/api';

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  userCount: number;
}

export default function UsersPage() {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [roleFilter, setRoleFilter] = React.useState<string>('all');
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [activeTab, setActiveTab] = React.useState<'users' | 'roles'>('users');

  const { data: usersData, isLoading, error, refetch } = useUsers({
    role: roleFilter !== 'all' ? roleFilter : undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
  });

  const users = usersData?.items || [];

  // Static roles data (could be fetched from API in the future)
  const roles: Role[] = [
    {
      id: 'role-admin',
      name: 'Admin',
      description: 'Full system access with all permissions',
      permissions: ['*'],
      userCount: users.filter((u) => u.role === 'admin').length,
    },
    {
      id: 'role-editor',
      name: 'Editor',
      description: 'Can create and modify pipelines, agents, and engagements',
      permissions: ['read', 'write', 'execute'],
      userCount: users.filter((u) => u.role === 'editor').length,
    },
    {
      id: 'role-viewer',
      name: 'Viewer',
      description: 'Read-only access to dashboards and reports',
      permissions: ['read'],
      userCount: users.filter((u) => u.role === 'viewer').length,
    },
    {
      id: 'role-api',
      name: 'API',
      description: 'Service accounts for automated integrations',
      permissions: ['read', 'write', 'execute'],
      userCount: users.filter((u) => u.role === 'api').length,
    },
  ];

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <ShieldCheck className="h-4 w-4 text-purple-500" />;
      case 'editor':
        return <Edit className="h-4 w-4 text-blue-500" />;
      case 'viewer':
        return <User className="h-4 w-4 text-gray-500" />;
      case 'api':
        return <Key className="h-4 w-4 text-orange-500" />;
      default:
        return <User className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-600 border-green-500/30';
      case 'inactive':
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/30';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-500/10 text-purple-600 border-purple-500/30';
      case 'editor':
        return 'bg-blue-500/10 text-blue-600 border-blue-500/30';
      case 'viewer':
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
      case 'api':
        return 'bg-orange-500/10 text-orange-600 border-orange-500/30';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/30';
    }
  };

  // Stats
  const stats = {
    total: users.length,
    active: users.filter((u) => u.status === 'active').length,
    inactive: users.filter((u) => u.status === 'inactive').length,
    pending: users.filter((u) => u.status === 'pending').length,
    mfaEnabled: users.filter((u) => u.mfa_enabled).length,
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
        <p className="text-lg font-medium">Failed to load users</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
        <Button onClick={() => refetch()}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/admin/settings">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Users & Access</h1>
            <p className="text-muted-foreground">
              Manage users, roles, and permissions
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Invite User
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-muted-foreground" />
              <div className="text-2xl font-bold">{stats.total}</div>
            </div>
            <p className="text-xs text-muted-foreground">Total Users</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-green-500" />
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
            </div>
            <p className="text-xs text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <UserX className="h-5 w-5 text-gray-500" />
              <div className="text-2xl font-bold text-gray-600">{stats.inactive}</div>
            </div>
            <p className="text-xs text-muted-foreground">Inactive</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-yellow-500" />
              <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            </div>
            <p className="text-xs text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-500" />
              <div className="text-2xl font-bold text-blue-600">{stats.mfaEnabled}</div>
            </div>
            <p className="text-xs text-muted-foreground">MFA Enabled</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('users')}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'users'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <Users className="mr-2 inline-block h-4 w-4" />
            Users
          </button>
          <button
            onClick={() => setActiveTab('roles')}
            className={cn(
              'border-b-2 px-4 py-2 text-sm font-medium transition-colors',
              activeTab === 'roles'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <Shield className="mr-2 inline-block h-4 w-4" />
            Roles
          </button>
        </div>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>All Users</CardTitle>
                <CardDescription>
                  {filteredUsers.length} users found
                </CardDescription>
              </div>
              <div className="flex flex-col gap-2 md:flex-row md:items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search users..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 w-64"
                  />
                </div>
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="all">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="editor">Editor</option>
                  <option value="viewer">Viewer</option>
                  <option value="api">API</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {filteredUsers.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No users found
              </div>
            ) : (
              <div className="rounded-md border overflow-x-auto">
                <table className="w-full min-w-[800px]">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="p-3 text-left text-sm font-medium">User</th>
                      <th className="p-3 text-left text-sm font-medium">Role</th>
                      <th className="p-3 text-left text-sm font-medium">Status</th>
                      <th className="p-3 text-left text-sm font-medium">Last Login</th>
                      <th className="p-3 text-left text-sm font-medium">MFA</th>
                      <th className="p-3 text-left text-sm font-medium">Created</th>
                      <th className="p-3 text-left text-sm font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((user) => (
                      <tr key={user.id} className="border-b last:border-0 hover:bg-muted/50">
                        <td className="p-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-medium">
                              {user.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                            </div>
                            <div>
                              <p className="font-medium">{user.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {user.email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="p-3">
                          <span
                            className={cn(
                              'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                              getRoleBadge(user.role)
                            )}
                          >
                            {getRoleIcon(user.role)}
                            {user.role}
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={cn(
                              'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium capitalize',
                              getStatusBadge(user.status)
                            )}
                          >
                            {user.status}
                          </span>
                        </td>
                        <td className="p-3 text-sm text-muted-foreground">
                          {user.last_login
                            ? new Date(user.last_login).toLocaleString()
                            : 'Never'}
                        </td>
                        <td className="p-3">
                          {user.mfa_enabled ? (
                            <Shield className="h-4 w-4 text-green-500" />
                          ) : (
                            <Shield className="h-4 w-4 text-gray-300" />
                          )}
                        </td>
                        <td className="p-3 text-sm text-muted-foreground">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="icon" title="Edit">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" title="Delete">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" title="More">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Roles Tab */}
      {activeTab === 'roles' && (
        <div className="grid gap-6 md:grid-cols-2">
          {roles.map((role) => (
            <Card key={role.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getRoleIcon(role.name.toLowerCase())}
                    <div>
                      <CardTitle className="text-lg">{role.name}</CardTitle>
                      <CardDescription>{role.description}</CardDescription>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon">
                    <Edit className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium mb-2">Permissions</p>
                    <div className="flex flex-wrap gap-2">
                      {role.permissions.map((permission) => (
                        <span
                          key={permission}
                          className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium"
                        >
                          {permission === '*' ? 'All Permissions' : permission}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between border-t pt-4">
                    <span className="text-sm text-muted-foreground">
                      {role.userCount} users with this role
                    </span>
                    <Button variant="outline" size="sm">
                      View Users
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
