import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: "up" | "down" | "neutral";
  positive?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({
  title,
  value,
  change,
  trend,
  positive,
  icon,
  className,
}: MetricCardProps) {
  const getTrendColor = () => {
    if (trend === "neutral") return "text-muted-foreground";
    const isPositive = positive !== undefined ? positive : trend === "up";
    return isPositive ? "text-green-600" : "text-red-600";
  };

  const TrendIcon =
    trend === "up" ? ArrowUp : trend === "down" ? ArrowDown : Minus;

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold">{value}</div>
          {change !== undefined && trend && (
            <div
              className={cn(
                "flex items-center text-xs font-medium",
                getTrendColor(),
              )}
            >
              <TrendIcon className="w-3 h-3 mr-1" />
              {change > 0 ? "+" : ""}
              {change}%
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
