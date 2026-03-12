"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useCriteria, useUpdateWeights } from "@/hooks/use-settings";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function ScoringWeightsTab() {
  const { data: criteria, isLoading } = useCriteria();
  const updateWeights = useUpdateWeights();
  const [weights, setWeights] = useState<Record<string, number>>({});

  useEffect(() => {
    if (criteria) {
      const w: Record<string, number> = {};
      for (const c of criteria) {
        w[c.id] = c.weight;
      }
      setWeights(w);
    }
  }, [criteria]);

  const total = Object.values(weights).reduce((sum, w) => sum + w, 0);
  const totalPercent = Math.round(total * 100);
  const isValid = Math.abs(total - 1) < 0.001;

  async function handleSave() {
    try {
      await updateWeights.mutateAsync({
        weights: Object.entries(weights).map(([id, weight]) => ({
          id,
          weight,
        })),
      });
      toast.success("가중치가 저장되었습니다");
    } catch {
      toast.error("저장에 실패했습니다");
    }
  }

  if (isLoading || !criteria) {
    return <div className="py-8 text-center text-muted-foreground">로딩 중...</div>;
  }

  return (
    <div className="space-y-6">
      {criteria
        .sort((a, b) => a.display_order - b.display_order)
        .map((c) => {
          const w = weights[c.id] ?? c.weight;
          return (
            <div key={c.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>{c.name}</Label>
                <span className="text-sm font-medium">
                  {Math.round(w * 100)}%
                </span>
              </div>
              {c.description && (
                <p className="text-xs text-muted-foreground">
                  {c.description}
                </p>
              )}
              <Slider
                value={[w * 100]}
                onValueChange={(val) => {
                  const v = Array.isArray(val) ? val[0] : val;
                  setWeights((prev) => ({ ...prev, [c.id]: v / 100 }));
                }}
                max={100}
                step={1}
              />
            </div>
          );
        })}

      <div className="flex items-center justify-between border-t pt-4">
        <span
          className={cn(
            "text-sm font-medium",
            isValid ? "text-green-600" : "text-red-600",
          )}
        >
          합계: {totalPercent}% {isValid ? "" : "(100%여야 합니다)"}
        </span>
        <Button
          onClick={handleSave}
          disabled={!isValid || updateWeights.isPending}
        >
          {updateWeights.isPending && (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          )}
          저장
        </Button>
      </div>
    </div>
  );
}
