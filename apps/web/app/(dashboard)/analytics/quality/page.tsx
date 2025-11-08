'use client'

import { KPICard } from '@/components/analytics/kpi-card'
import { LineChart } from '@/components/charts/line-chart'
import { BarChart } from '@/components/charts/bar-chart'
import { DataTable, Column } from '@/components/table/data-table'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Download, Star, ThumbsUp, AlertTriangle, TrendingUp } from 'lucide-react'
import { downloadCSV } from '@/lib/utils'

interface QualityEntry {
  agent: string
  qualityScore: number
  codeQuality: number
  testCoverage: number
  reviewScore: number
  issues: number
  trend: 'up' | 'down' | 'stable'
}

const qualityData: QualityEntry[] = [
  { agent: 'Code Generator', qualityScore: 94, codeQuality: 92, testCoverage: 88, reviewScore: 95, issues: 3, trend: 'up' },
  { agent: 'Test Writer', qualityScore: 98, codeQuality: 97, testCoverage: 99, reviewScore: 98, issues: 1, trend: 'stable' },
  { agent: 'Code Reviewer', qualityScore: 91, codeQuality: 89, testCoverage: 85, reviewScore: 93, issues: 5, trend: 'down' },
  { agent: 'Bug Fixer', qualityScore: 96, codeQuality: 94, testCoverage: 92, reviewScore: 97, issues: 2, trend: 'up' },
  { agent: 'Documentation', qualityScore: 99, codeQuality: 98, testCoverage: 95, reviewScore: 99, issues: 0, trend: 'stable' },
]

const qualityTrendData = [
  { date: 'Feb 5', quality: 92, coverage: 87, review: 94 },
  { date: 'Feb 6', quality: 93, coverage: 88, review: 94 },
  { date: 'Feb 7', quality: 92, coverage: 89, review: 95 },
  { date: 'Feb 8', quality: 94, coverage: 89, review: 95 },
  { date: 'Feb 9', quality: 94, coverage: 90, review: 96 },
  { date: 'Feb 10', quality: 95, coverage: 91, review: 96 },
  { date: 'Feb 11', quality: 95, coverage: 92, review: 97 },
  { date: 'Feb 12', quality: 96, coverage: 92, review: 97 },
]

const issuesByType = [
  { type: 'Code Style', count: 12 },
  { type: 'Logic Errors', count: 5 },
  { type: 'Performance', count: 8 },
  { type: 'Security', count: 2 },
  { type: 'Documentation', count: 6 },
]

const columns: Column<QualityEntry>[] = [
  { key: 'agent', header: 'Agent', sortable: true },
  {
    key: 'qualityScore',
    header: 'Quality Score',
    sortable: true,
    cell: (row) => (
      <div className="flex items-center gap-2">
        <span className="font-semibold">{row.qualityScore}</span>
        {row.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
        {row.trend === 'down' && <AlertTriangle className="h-4 w-4 text-red-600" />}
      </div>
    ),
  },
  {
    key: 'codeQuality',
    header: 'Code Quality',
    sortable: true,
    cell: (row) => `${row.codeQuality}%`,
  },
  {
    key: 'testCoverage',
    header: 'Test Coverage',
    sortable: true,
    cell: (row) => `${row.testCoverage}%`,
  },
  {
    key: 'reviewScore',
    header: 'Review Score',
    sortable: true,
    cell: (row) => `${row.reviewScore}%`,
  },
  {
    key: 'issues',
    header: 'Issues',
    sortable: true,
    cell: (row) => (
      <Badge variant={row.issues === 0 ? 'success' : row.issues < 3 ? 'warning' : 'danger'}>
        {row.issues}
      </Badge>
    ),
  },
]

export default function QualityPage() {
  const handleExport = () => {
    const exportData = qualityData.map(item => ({
      Agent: item.agent,
      'Quality Score': item.qualityScore,
      'Code Quality (%)': item.codeQuality,
      'Test Coverage (%)': item.testCoverage,
      'Review Score (%)': item.reviewScore,
      Issues: item.issues,
    }))
    downloadCSV(exportData, 'quality-metrics.csv')
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Quality Metrics</h1>
          <p className="text-muted-foreground">
            Track code quality, test coverage, and review scores
          </p>
        </div>
        <div className="flex gap-3">
          <Select defaultValue="30d" className="w-40">
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
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
          title="Overall Quality"
          value="96"
          change={4.2}
          trend="up"
          positive={true}
          icon={<Star className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Test Coverage"
          value="92%"
          change={3.5}
          trend="up"
          positive={true}
          icon={<ThumbsUp className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Review Score"
          value="97%"
          change={2.1}
          trend="up"
          positive={true}
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Open Issues"
          value="11"
          change={-18}
          trend="down"
          positive={true}
          icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <LineChart
          title="Quality Trends"
          description="Overall quality, coverage, and review scores over time"
          data={qualityTrendData}
          xAxisKey="date"
          dataKeys={[
            { key: 'quality', color: '#4F46E5', label: 'Quality Score' },
            { key: 'coverage', color: '#10B981', label: 'Test Coverage (%)' },
            { key: 'review', color: '#06B6D4', label: 'Review Score (%)' },
          ]}
        />
        <BarChart
          title="Issues by Type"
          description="Distribution of issues across categories"
          data={issuesByType}
          xAxisKey="type"
          dataKeys={[
            { key: 'count', color: '#F59E0B', label: 'Issue Count' },
          ]}
        />
      </div>

      {/* Quality Table */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Agent Quality Metrics</h2>
        <DataTable data={qualityData} columns={columns} />
      </div>
    </div>
  )
}
