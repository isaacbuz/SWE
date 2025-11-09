import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface SuggestionCardProps {
  title: string;
  description?: string;
  priority?: "high" | "medium" | "low";
  category?: string;
  onAccept?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function SuggestionCard({
  title,
  description,
  priority = "medium",
  category,
  onAccept,
  onDismiss,
  className,
}: SuggestionCardProps) {
  const priorityColors = {
    high: "destructive",
    medium: "warning",
    low: "secondary",
  } as const;

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="mt-1 p-2 rounded-md bg-primary/10">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div className="flex-1">
              <CardTitle className="text-base font-semibold">{title}</CardTitle>
              {description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {description}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {category && <Badge variant="outline">{category}</Badge>}
            <Badge variant={priorityColors[priority]}>{priority}</Badge>
          </div>
        </div>
      </CardHeader>
      {(onAccept || onDismiss) && (
        <CardFooter className="pt-0 gap-2">
          {onAccept && (
            <Button onClick={onAccept} size="sm">
              Accept
            </Button>
          )}
          {onDismiss && (
            <Button onClick={onDismiss} variant="ghost" size="sm">
              Dismiss
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
