import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface WizardNavigationProps {
  currentStep: number;
  totalSteps: number;
  onBack?: () => void;
  onNext?: () => void;
  onComplete?: () => void;
  canGoBack?: boolean;
  canGoNext?: boolean;
  isLoading?: boolean;
  className?: string;
}

export function WizardNavigation({
  currentStep,
  totalSteps,
  onBack,
  onNext,
  onComplete,
  canGoBack = true,
  canGoNext = true,
  isLoading = false,
  className,
}: WizardNavigationProps) {
  const isLastStep = currentStep === totalSteps;
  const isFirstStep = currentStep === 1;

  return (
    <div
      className={cn(
        "flex items-center justify-between pt-6 border-t",
        className,
      )}
    >
      <Button
        variant="outline"
        onClick={onBack}
        disabled={isFirstStep || !canGoBack || isLoading}
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>

      {isLastStep ? (
        <Button onClick={onComplete} disabled={!canGoNext || isLoading}>
          {isLoading ? "Processing..." : "Complete"}
        </Button>
      ) : (
        <Button onClick={onNext} disabled={!canGoNext || isLoading}>
          Next
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      )}
    </div>
  );
}
