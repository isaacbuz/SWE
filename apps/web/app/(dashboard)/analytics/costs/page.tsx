'use client'

import { KPICard } from '@/components/analytics/kpi-card'
import { LineChart } from '@/components/charts/line-chart'
import { PieChart } from '@/components/charts/pie-chart'
import { DataTable, Column } from '@/components/table/data-table'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Download, DollarSign, TrendingDown, Calendar } from 'lucide-react'
import { formatCurrency, downloadCSV } from '@/lib/utils'

interface CostEntry {
  date: string
  model: string
  requests: number
  tokens: number
  cost: number
  project: string
}

const costData: CostEntry[] = [
  { date: '2024-02-12', model: 'Claude Sonnet 4.5', requests: 145, tokens: 52000, cost: 15.60, project: 'Project Alpha' },
  { date: '2024-02-12', model: 'GPT-5', requests: 89, tokens: 38000, cost: 12.45, project: 'Project Beta' },
  { date: '2024-02-12', model: 'Claude Haiku', requests: 423, tokens: 125000, cost: 8.75, project: 'Project Gamma' },
  { date: '2024-02-11', model: 'Claude Sonnet 4.5', requests: 132, tokens: 48000, cost: 14.40, project: 'Project Alpha' },
  { date: '2024-02-11', model: 'GPT-4o', requests: 67, tokens: 29000, cost: 9.85, project: 'Project Delta' },
]

const dailyCostData = [
  { date: 'Feb 5', cost: 55.3, budget: 60 },
  { date: 'Feb 6', cost: 48.7, budget: 60 },
  { date: 'Feb 7', cost: 52.4, budget: 60 },
  { date: 'Feb 8', cost: 49.1, budget: 60 },
  { date: 'Feb 9', cost: 53.8, budget: 60 },
  { date: 'Feb 10', cost: 47.2, budget: 60 },
  { date: 'Feb 11', cost: 51.5, budget: 60 },
  { date: 'Feb 12', cost: 46.6, budget: 60 },
]

const modelDistribution = [
  { name: 'Claude Sonnet 4.5', value: 127.42 },
  { name: 'GPT-5', value: 98.56 },
  { name: 'Claude Haiku', value: 45.23 },
  { name: 'GPT-4o', value: 76.89 },
]

const columns: Column<CostEntry>[] = [
  { key: 'date', header: 'Date', sortable: true },
  { key: 'model', header: 'Model', sortable: true },
  { key: 'project', header: 'Project', sortable: true },
  { key: 'requests', header: 'Requests', sortable: true },
  {
    key: 'tokens',
    header: 'Tokens',
    sortable: true,
    cell: (row) => row.tokens.toLocaleString(),
  },
  {
    key: 'cost',
    header: 'Cost',
    sortable: true,
    cell: (row) => formatCurrency(row.cost),
  },
]

export default function CostsPage() {
  const handleExport = () => {
    const exportData = costData.map(item => ({
      Date: item.date,
      Model: item.model,
      Project: item.project,
      Requests: item.requests,
      Tokens: item.tokens,
      'Cost ($)': item.cost,
    }))
    downloadCSV(exportData, 'cost-breakdown.csv')
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cost Analytics</h1>
          <p className="text-muted-foreground">
            Detailed breakdown of AI model costs and usage
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
      <div className="grid gap-4 md:grid-cols-3">
        <KPICard
          title="Total Spend (MTD)"
          value="$348.10"
          change={-8.5}
          trend="down"
          positive={true}
          icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Avg Daily Cost"
          value="$51.90"
          change={-12}
          trend="down"
          positive={true}
          icon={<TrendingDown className="h-4 w-4 text-muted-foreground" />}
        />
        <KPICard
          title="Budget Remaining"
          value="$1,651.90"
          change={undefined}
          icon={<Calendar className="h-4 w-4 text-muted-foreground" />}
        />
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <LineChart
          title="Daily Cost vs Budget"
          description="Track spending against your daily budget"
          data={dailyCostData}
          xAxisKey="date"
          dataKeys={[
            { key: 'cost', color: '#4F46E5', label: 'Actual Cost ($)' },
            { key: 'budget', color: '#10B981', label: 'Budget ($)' },
          ]}
        />
        <PieChart
          title="Cost by Model"
          description="Distribution of spending across AI models"
          data={modelDistribution}
          dataKey="value"
          nameKey="name"
        />
      </div>

      {/* Cost Breakdown Table */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Cost Breakdown</h2>
        <DataTable data={costData} columns={columns} />
      </div>
    </div>
  )
}
