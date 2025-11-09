import { TrendingDown, TrendingUp } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-ink-primary">Analytics</h1>
        <p className="mt-2 text-ink-secondary">
          Track performance, costs, and quality metrics
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <select className="rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary">
          <option>Last 30 days</option>
          <option>Last 7 days</option>
          <option>Last 90 days</option>
          <option>All time</option>
        </select>
        <select className="rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary">
          <option>All Models</option>
          <option>GPT-4</option>
          <option>Claude</option>
          <option>Gemini</option>
        </select>
        <select className="rounded-md border border-border-default bg-surface-secondary px-4 py-2 text-sm text-ink-primary focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary">
          <option>All Projects</option>
          <option>E-Commerce</option>
          <option>Mobile App</option>
          <option>API Gateway</option>
        </select>
      </div>

      {/* KPI Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Spend"
          value="$127.42"
          change="-12%"
          trend="down"
          positive
        />
        <KPICard
          title="PR Merge Rate"
          value="89%"
          change="+4%"
          trend="up"
          positive
        />
        <KPICard
          title="Avg MTTR"
          value="42min"
          change="-8min"
          trend="down"
          positive
        />
        <KPICard
          title="Agent Utilization"
          value="76%"
          change="+2%"
          trend="up"
          positive
        />
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Cost by Model" />
        <ChartCard title="Agent Success Rate" />
        <ChartCard title="Pipeline Health" />
        <ChartCard title="Quality Trends" />
      </div>
    </div>
  );
}

function KPICard({
  title,
  value,
  change,
  trend,
  positive,
}: {
  title: string;
  value: string;
  change: string;
  trend: "up" | "down";
  positive: boolean;
}) {
  const TrendIcon = trend === "up" ? TrendingUp : TrendingDown;
  const trendColor = positive ? "text-status-success" : "text-status-danger";

  return (
    <div className="rounded-lg border border-border-default bg-surface-secondary p-6">
      <p className="text-sm font-medium text-ink-tertiary">{title}</p>
      <div className="mt-2 flex items-baseline justify-between">
        <p className="text-3xl font-bold text-ink-primary">{value}</p>
        <div
          className={
            "flex items-center gap-1 text-sm font-medium " + trendColor
          }
        >
          <TrendIcon className="h-4 w-4" />
          <span>{change}</span>
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title }: { title: string }) {
  return (
    <div className="rounded-lg border border-border-default bg-surface-secondary p-6">
      <h3 className="text-lg font-semibold text-ink-primary">{title}</h3>
      <div className="mt-6 flex h-64 items-center justify-center rounded-md bg-surface-tertiary">
        <p className="text-sm text-ink-tertiary">
          Chart placeholder - Add Recharts
        </p>
      </div>
    </div>
  );
}
