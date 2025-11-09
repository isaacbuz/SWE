"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface SparklineProps {
  title: string;
  data: Array<{ value: number }>;
  value?: string | number;
  trend?: "up" | "down" | "neutral";
  color?: string;
  className?: string;
}

export function Sparkline({
  title,
  data,
  value,
  trend,
  color = "#4F46E5",
  className,
}: SparklineProps) {
  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {value && <div className="text-2xl font-bold">{value}</div>}
          <div className="h-[60px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={color}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
