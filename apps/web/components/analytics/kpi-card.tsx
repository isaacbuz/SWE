import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowDown, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: "up" | "down";
  positive?: boolean;
  icon?: React.ReactNode;
}

export function KPICard({
  title,
  value,
  change,
  trend,
  positive,
  icon,
}: KPICardProps) {
  const isPositiveChange = positive !== undefined ? positive : trend === "up";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
            {trend === "up" && (
              <ArrowUp
                className={cn(
                  "h-4 w-4",
                  isPositiveChange ? "text-green-600" : "text-red-600",
                )}
              />
            )}
            {trend === "down" && (
              <ArrowDown
                className={cn(
                  "h-4 w-4",
                  isPositiveChange ? "text-green-600" : "text-red-600",
                )}
              />
            )}
            <span
              className={cn(
                isPositiveChange ? "text-green-600" : "text-red-600",
              )}
            >
              {change > 0 ? "+" : ""}
              {change}%
            </span>
            <span>from last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
