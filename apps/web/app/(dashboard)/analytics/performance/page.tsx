'use client'

import { KPICard } from '@/components/analytics/kpi-card'
import { LineChart } from '@/components/charts/line-chart'
import { BarChart } from '@/components/charts/bar-chart'
import { DataTable, Column } from '@/components/table/data-table'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Download, Clock, Zap, Activity, CheckCircle } from 'lucide-react'
import { downloadCSV } from '@/lib/utils'

interface PerformanceEntry {
  agent: string
  avgLatency: number
  p95Latency: number
  successRate: number
  totalRequests: number
  status: 'healthy' | 'warning' | 'critical'
}

const performanceData: PerformanceEntry[] = [
  { agent: 'Code Generator', avgLatency: 245, p95Latency: 512, successRate: 99.4, totalRequests: 3420, status: 'healthy' },
  { agent: 'Test Writer', avgLatency: 189, p95Latency: 398, successRate: 99.8, totalRequests: 2180, status: 'healthy' },
  { agent: 'Code Reviewer', avgLatency: 312, p95Latency: 687, successRate: 98.2, totalRequests: 1890, status: 'warning' },
  { agent: 'Bug Fixer', avgLatency: 278, p95Latency: 589, successRate: 99.1, totalRequests: 1560, status: 'healthy' },
  { agent: 'Documentation', avgLatency: 156, p95Latency: 289, successRate: 99.9, totalRequests: 4250, status: 'healthy' },
]

const latencyTrendData = [
  { date: 'Feb 5', avg: 229, p95: 487 },
  { date: 'Feb 6', avg: 238, p95: 502 },
  { date: 'Feb 7', avg: 233, p95: 495 },
  { date: 'Feb 8', avg: 241, p95: 508 },
  { date: 'Feb 9', avg: 235, p95: 498 },
  { date: 'Feb 10', avg: 228, p95: 485 },
  { date: 'Feb 11', avg: 232, p95: 492 },
  { date: 'Feb 12', avg: 226, p95: 479 },
]

const throughputData = [
  { hour: '00:00', requests: 145 },
  { hour: '03:00', requests: 89 },
  { hour: '06:00', requests: 234 },
  { hour: '09:00', requests: 567 },
  { hour: '12:00', requests: 789 },
  { hour: '15:00', requests: 892 },
  { hour: '18:00', requests: 645 },
  { hour: '21:00', requests: 423 },
]

const columns: Column<PerformanceEntry>[] = [
  { key: 'agent', header: 'Agent', sortable: true },
  {
    key: 'avgLatency',
    header: 'Avg Latency',
    sortable: true,
    cell: (row) => `${row.avgLatency}ms`,
  },
  {
    key: 'p95Latency',
    header: 'P95 Latency',
    sortable: true,
    cell: (row) => `${row.p95Latency}ms`,
  },
  {
    key: 'successRate',
    header: 'Success Rate',
    sortable: true,
    cell: (row) => `${row.successRate}%`,
  },
  {
    key: 'totalRequests',
    header: 'Total Requests',
    sortable: true,
    cell: (row) => row.totalRequests.toLocaleString(),
  },
  {
    key: 'status',
    header: 'Status',
    cell: (row) => (
      <Badge
        variant={
          row.status === 'healthy'
            ? 'success'
            : row.status === 'warning'
            ? 'warning'
            : 'danger'
        }
      >
        {row.status}
      </Badge>
    ),
  },
]

export default function PerformancePage() {
  const handleExport = () => {
    const exportData = performanceData.map(item => ({
      Agent: item.agent,
      'Avg Latency (ms)': item.avgLatency,
      'P95 Latency (ms)': item.p95Latency,
      'Success Rate (%)': item.successRate,
      'Total Requests': item.totalRequests,
      Status: item.status,
    }))
    downloadCSV(exportData, 'performance-metrics.csv')
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Performance Metrics</h1>
          <p className="text-muted-foreground">
            Monitor latency, throughput, and success rates
          </p>
        </div>
        <div className="flex gap-3">
          <Select defaultValue="24h" className="w-40">
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </Select>
          <Button onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <KPICard
          title="Avg Response Time"
          value="226ms"
          change={-8}
          trend="down"
          positive={true}
          icon={<Clock className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="P95 Latency"
          value="479ms"
          change={-5.2}
          trend="down"
          positive={true}
          icon={<Zap className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Success Rate"
          value="99.4%"
          change={1.2}
          trend="up"
          positive={true}
          icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Requests/Hour"
          value="892"
          change={15}
          trend="up"
          positive={true}
          icon={<Activity className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <LineChart
          title="Latency Trends"
          description="Average and P95 latency over time"
          data={latencyTrendData}
          xAxisKey="date"
          dataKeys={[
            { key: 'avg', color: '#4F46E5', label: 'Avg Latency (ms)' },
            { key: 'p95', color: '#F59E0B', label: 'P95 Latency (ms)' },
          ]}
        />
        <BarChart
          title="Request Throughput"
          description="Requests per hour throughout the day"
          data={throughputData}
          xAxisKey="hour"
          dataKeys={[
            { key: 'requests', color: '#10B981', label: 'Requests' },
          ]}
        />
      </div>

      {/* Performance Table */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Agent Performance</h2>
        <DataTable data={performanceData} columns={columns} />
      </div>
    </div>
  )
}
