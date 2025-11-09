'use client'

import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { DataTable, Column } from '@/components/table/data-table'
import { Badge } from '@/components/ui/badge'
import { Plus, Copy, Eye, EyeOff, Trash2, Calendar, Key } from 'lucide-react'

interface APIKey {
  id: string
  name: string
  key: string
  created: string
  lastUsed: string
  status: 'active' | 'revoked'
  permissions: string[]
}

const seedKeys: APIKey[] = [
  {
    id: '1',
    name: 'Production Key',
    key: 'sk_prod_abc123***',
    created: '2024-01-15',
    lastUsed: '2024-02-12 14:30',
    status: 'active',
    permissions: ['read', 'write', 'delete'],
  },
  {
    id: '2',
    name: 'Development Key',
    key: 'sk_dev_xyz789***',
    created: '2024-02-01',
    lastUsed: '2024-02-12 16:45',
    status: 'active',
    permissions: ['read', 'write'],
  },
  {
    id: '3',
    name: 'Test Key',
    key: 'sk_test_def456***',
    created: '2024-01-20',
    lastUsed: '2024-02-10 09:15',
    status: 'active',
    permissions: ['read'],
  },
  {
    id: '4',
    name: 'Old Production Key',
    key: 'sk_prod_old***',
    created: '2023-12-01',
    lastUsed: '2024-01-15 10:00',
    status: 'revoked',
    permissions: ['read', 'write'],
  },
]

const defaultPermissions = {
  read: true,
  write: true,
  delete: false,
}

export default function APIKeysPage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())
  const [keys, setKeys] = useState<APIKey[]>(seedKeys)
  const [keyName, setKeyName] = useState('')
  const [permissions, setPermissions] = useState(defaultPermissions)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const activeKeys = useMemo(
    () => keys.filter((key) => key.status === 'active').length,
    [keys]
  )

  const columns: Column<APIKey>[] = [
    { key: 'name', header: 'Name', sortable: true },
    {
      key: 'key',
      header: 'API Key',
      cell: (row) => {
        const masked = row.key.replace(/.(?=.{4})/g, '*')
        return (
          <div className="flex items-center gap-2">
            <code className="rounded bg-muted px-2 py-1 text-sm font-mono tracking-tight">
              {visibleKeys.has(row.id) ? row.key : masked}
            </code>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => toggleKeyVisibility(row.id)}
              aria-label={visibleKeys.has(row.id) ? 'Hide key' : 'Show key'}
            >
              {visibleKeys.has(row.id) ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => copyToClipboard(row.key)}
              aria-label="Copy key"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      cell: (row) => (
        <Badge variant={row.status === 'active' ? 'success' : 'outline'}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'created',
      header: 'Created',
      sortable: true,
      cell: (row) => new Date(row.created).toLocaleDateString(),
    },
    {
      key: 'lastUsed',
      header: 'Last Used',
      sortable: true,
    },
    {
      key: 'actions',
      header: '',
      cell: (row) => (
        <div className="flex justify-end">
          {row.status === 'active' ? (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => revokeKey(row.id)}
              aria-label="Revoke key"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          ) : (
            <Badge variant="outline" className="text-xs uppercase tracking-tight">
              Revoked
            </Badge>
          )}
        </div>
      ),
    },
  ]

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys((prev) => {
      const next = new Set(prev)
      if (next.has(keyId)) {
        next.delete(keyId)
      } else {
        next.add(keyId)
      }
      return next
    })
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('API key copied to clipboard', { duration: 2000 })
    } catch {
      toast.error('Unable to copy key')
    }
  }

  const handlePermissionChange = (perm: keyof typeof permissions) => {
    setPermissions((prev) => ({ ...prev, [perm]: !prev[perm] }))
  }

  const generateKey = () => {
    const random = crypto.getRandomValues(new Uint32Array(3))
    return `sk_${Array.from(random)
      .map((chunk) => chunk.toString(16))
      .join('')
      .slice(0, 16)}***`
  }

  const handleCreateKey = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!keyName.trim()) return

    setIsSubmitting(true)
    setTimeout(() => {
      const newKey: APIKey = {
        id: crypto.randomUUID(),
        name: keyName.trim(),
        key: generateKey(),
        created: new Date().toISOString(),
        lastUsed: 'Never',
        status: 'active',
        permissions: Object.entries(permissions)
          .filter(([, allowed]) => allowed)
          .map(([perm]) => perm),
      }

      setKeys((prev) => [newKey, ...prev])
      setKeyName('')
      setPermissions(defaultPermissions)
      setShowCreateForm(false)
      setIsSubmitting(false)

      toast.success('API key created securely. Copy it now — you will not see it again.', {
        duration: 3500,
      })
    }, 350)
  }

  const revokeKey = (keyId: string) => {
    setKeys((prev) =>
      prev.map((key) =>
        key.id === keyId
          ? { ...key, status: 'revoked', lastUsed: new Date().toISOString() }
          : key
      )
    )
    toast.warning('API key revoked', { duration: 2500 })
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
          <p className="text-muted-foreground">
            Manage programmatic access with strict least-privilege controls.
          </p>
        </div>
        <Button onClick={() => setShowCreateForm((prev) => !prev)}>
          <Plus className="mr-2 h-4 w-4" />
          {showCreateForm ? 'Hide form' : 'Create API Key'}
        </Button>
      </div>

      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create new API key</CardTitle>
            <CardDescription>Keys are generated once. Store them securely.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="keyName">Key name</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="keyName"
                    placeholder="Production API Key"
                    className="pl-9"
                    value={keyName}
                    onChange={(event) => setKeyName(event.target.value)}
                    maxLength={80}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Use a descriptive label so teammates recognize the key later.
                </p>
              </div>

              <div className="space-y-2">
                <Label>Permissions</Label>
                <div className="space-y-2">
                  <PermissionToggle
                    id="perm-read"
                    label="Read — View data and resources"
                    checked={permissions.read}
                    onChange={() => handlePermissionChange('read')}
                  />
                  <PermissionToggle(
                    id="perm-write"
                    label="Write — Modify resources"
                    checked={permissions.write}
                    onChange={() => handlePermissionChange('write')}
                  />
                  <PermissionToggle
                    id="perm-delete"
                    label="Delete — Remove resources"
                    checked={permissions.delete}
                    onChange={() => handlePermissionChange('delete')}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={
                    !keyName.trim() ||
                    !Object.values(permissions).some(Boolean) ||
                    isSubmitting
                  }
                >
                  {isSubmitting ? 'Creating…' : 'Create key'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Usage overview</CardTitle>
          <CardDescription>Keep secrets rotated and revoke unused keys.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <UsageStat
              label="Active keys"
              value={activeKeys}
              helper={`${keys.length - activeKeys} revoked`}
            />
            <UsageStat
              label="Most recent key"
              value={keys[0]?.name ?? 'N/A'}
              helper={keys[0]?.created?.slice(0, 10) ?? ''}
            />
            <UsageStat
              label="Permissions per key"
              value={(
                keys.reduce((sum, key) => sum + key.permissions.length, 0) / keys.length
              ).toFixed(1)}
              helper="Aim for least privilege"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API keys</CardTitle>
          <CardDescription>Rotate keys regularly and never share secrets in plaintext.</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} data={keys} emptyMessage="No API keys created yet" />
        </CardContent>
      </Card>
    </div>
  )
}

function PermissionToggle({
  id,
  label,
  checked,
  onChange,
}: {
  id: string
  label: string
  checked: boolean
  onChange: () => void
}) {
  return (
    <label htmlFor={id} className="flex items-center gap-3 text-sm text-muted-foreground">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-4 w-4 rounded border border-border-default accent-brand-primary"
      />
      {label}
    </label>
  )
}

function UsageStat({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border border-border-default bg-surface-secondary p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-ink-tertiary">
        <Calendar className="h-3 w-3" />
        {label}
      </div>
      <p className="text-xl font-semibold text-ink-primary">{value}</p>
      {helper && <p className="text-xs text-ink-tertiary">{helper}</p>}
    </div>
  )
}
