'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable, Column } from '@/components/table/data-table'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/ui/select'
import { UserPlus, Mail, MoreVertical, Trash2 } from 'lucide-react'
import { useState } from 'react'

interface TeamMember {
  id: string
  name: string
  email: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  status: 'active' | 'invited' | 'inactive'
  joinedDate: string
}

const teamMembers: TeamMember[] = [
  {
    id: '1',
    name: 'Isaac Buz',
    email: 'isaac@example.com',
    role: 'owner',
    status: 'active',
    joinedDate: '2024-01-15',
  },
  {
    id: '2',
    name: 'Sarah Chen',
    email: 'sarah@example.com',
    role: 'admin',
    status: 'active',
    joinedDate: '2024-01-20',
  },
  {
    id: '3',
    name: 'Mike Johnson',
    email: 'mike@example.com',
    role: 'member',
    status: 'active',
    joinedDate: '2024-02-01',
  },
  {
    id: '4',
    name: 'Emily Davis',
    email: 'emily@example.com',
    role: 'member',
    status: 'invited',
    joinedDate: '2024-02-10',
  },
  {
    id: '5',
    name: 'Alex Kumar',
    email: 'alex@example.com',
    role: 'viewer',
    status: 'active',
    joinedDate: '2024-02-05',
  },
]

export default function TeamSettingsPage() {
  const [showInviteForm, setShowInviteForm] = useState(false)

  const columns: Column<TeamMember>[] = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
    },
    {
      key: 'email',
      header: 'Email',
      sortable: true,
    },
    {
      key: 'role',
      header: 'Role',
      sortable: true,
      cell: (row) => (
        <Badge
          variant={
            row.role === 'owner'
              ? 'default'
              : row.role === 'admin'
              ? 'info'
              : 'outline'
          }
        >
          {row.role}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      cell: (row) => (
        <Badge
          variant={
            row.status === 'active'
              ? 'success'
              : row.status === 'invited'
              ? 'warning'
              : 'outline'
          }
        >
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'joinedDate',
      header: 'Joined',
      sortable: true,
      cell: (row) => new Date(row.joinedDate).toLocaleDateString(),
    },
    {
      key: 'actions',
      header: '',
      cell: (row) => (
        <div className="flex justify-end gap-2">
          {row.role !== 'owner' && (
            <>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon">
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-8 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Team Management</h1>
          <p className="text-muted-foreground">
            Manage your team members and their permissions
          </p>
        </div>
        <Button onClick={() => setShowInviteForm(!showInviteForm)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite Member
        </Button>
      </div>

      {/* Invite Form */}
      {showInviteForm && (
        <Card>
          <CardHeader>
            <CardTitle>Invite Team Member</CardTitle>
            <CardDescription>
              Send an invitation to join your team
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="inviteEmail" className="text-sm font-medium">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="inviteEmail"
                    type="email"
                    placeholder="colleague@example.com"
                    className="pl-9"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label htmlFor="inviteRole" className="text-sm font-medium">
                  Role
                </label>
                <Select id="inviteRole" defaultValue="member">
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </Select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button>Send Invitation</Button>
              <Button variant="outline" onClick={() => setShowInviteForm(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Team Members Table */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members ({teamMembers.length})</CardTitle>
          <CardDescription>
            View and manage all team members
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable data={teamMembers} columns={columns} />
        </CardContent>
      </Card>

      {/* Role Permissions */}
      <Card>
        <CardHeader>
          <CardTitle>Role Permissions</CardTitle>
          <CardDescription>
            Understand what each role can do
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <Badge variant="default">Owner</Badge>
              <div>
                <p className="font-medium">Full Access</p>
                <p className="text-sm text-muted-foreground">
                  Can manage all aspects including billing and team settings
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Badge variant="info">Admin</Badge>
              <div>
                <p className="font-medium">Administrative Access</p>
                <p className="text-sm text-muted-foreground">
                  Can manage team members, projects, and integrations
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Badge variant="outline">Member</Badge>
              <div>
                <p className="font-medium">Standard Access</p>
                <p className="text-sm text-muted-foreground">
                  Can create and manage their own projects and agents
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Badge variant="outline">Viewer</Badge>
              <div>
                <p className="font-medium">Read-Only Access</p>
                <p className="text-sm text-muted-foreground">
                  Can view projects and analytics but cannot make changes
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
