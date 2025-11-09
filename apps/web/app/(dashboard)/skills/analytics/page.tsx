'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, TrendingUp, TrendingDown, Users, Zap, DollarSign, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import Link from 'next/link'
import { useSkillAnalytics } from '@/lib/hooks/use-skills'

const timeRanges = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
  { value: '365', label: 'Last year' },
]

export default function SkillsAnalyticsPage() {
  const params = useParams()
  const router = useRouter()
  const skillId = params.id as string
  
  const [timeRange, setTimeRange] = useState('30')
  const [startDate, setStartDate] = useState<string>()
  const [endDate, setEndDate] = useState<string>()
  
  // Calculate dates based on time range
  const getDateRange = (days: number) => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - days)
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    }
  }
  
  const dateRange = timeRange ? getDateRange(parseInt(timeRange)) : undefined
  
  const { data: analytics, isLoading, error } = useSkillAnalytics(
    skillId,
    dateRange ? { start_date: dateRange.start, end_date: dateRange.end } : undefined
  )

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">Loading analytics...</div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-destructive">
          Failed to load analytics. {error?.message}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 max-w-6xl">
      <div className="mb-6">
        <Link href={`/skills/${skillId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Skill
          </Button>
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Skill Analytics</h1>
        <p className="text-muted-foreground">
          Performance metrics and usage statistics
        </p>
      </div>

      {/* Time Range Selector */}
      <div className="mb-6">
        <Select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="w-48"
        >
          {timeRanges.map((range) => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </Select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Executions</span>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold">{analytics.executions.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {analytics.executions_success || 0} successful
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Installations</span>
            <Users className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold">{analytics.installations.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground mt-1">
            Total installations
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Avg Latency</span>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold">
            {analytics.avg_latency_ms ? `${analytics.avg_latency_ms}ms` : 'N/A'}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            P95: {analytics.p95_latency_ms || 0}ms
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Total Cost</span>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="text-2xl font-bold">
            ${analytics.total_cost_usd?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            ${analytics.avg_cost_per_execution?.toFixed(4) || '0.0000'} per execution
          </div>
        </div>
      </div>

      {/* Rating Breakdown */}
      {analytics.review_count > 0 && (
        <div className="bg-card border rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Rating Distribution</h2>
          <div className="space-y-2">
            {[5, 4, 3, 2, 1].map((rating) => {
              const count = analytics.rating_breakdown?.[rating] || 0
              const percentage = analytics.review_count > 0 
                ? (count / analytics.review_count) * 100 
                : 0
              return (
                <div key={rating} className="flex items-center gap-4">
                  <div className="w-12 text-sm">{rating} ⭐</div>
                  <div className="flex-1 bg-muted rounded-full h-4 relative">
                    <div
                      className="bg-primary h-4 rounded-full"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <div className="w-16 text-sm text-right">{count}</div>
                </div>
              )
            })}
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Average Rating: {analytics.avg_rating.toFixed(1)} / 5.0
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      <div className="bg-card border rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-muted-foreground">P50 Latency</div>
            <div className="text-lg font-semibold">
              {analytics.p50_latency_ms || 0}ms
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">P95 Latency</div>
            <div className="text-lg font-semibold">
              {analytics.p95_latency_ms || 0}ms
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">P99 Latency</div>
            <div className="text-lg font-semibold">
              {analytics.p99_latency_ms || 0}ms
            </div>
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Unique Users</div>
            <div className="text-lg font-semibold">
              {analytics.unique_users || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Success Rate */}
      {analytics.executions > 0 && (
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Success Rate</h2>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-sm">Success</span>
                <span className="text-sm font-semibold">
                  {analytics.executions_success || 0} / {analytics.executions}
                </span>
              </div>
              <div className="bg-muted rounded-full h-4 relative">
                <div
                  className="bg-green-500 h-4 rounded-full"
                  style={{
                    width: `${((analytics.executions_success || 0) / analytics.executions) * 100}%`,
                  }}
                />
              </div>
            </div>
            <div className="text-2xl font-bold">
              {(((analytics.executions_success || 0) / analytics.executions) * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

