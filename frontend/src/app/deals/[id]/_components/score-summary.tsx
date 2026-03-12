"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadarChart } from "@/components/common/radar-chart";
import { VerdictBadge } from "@/components/common/verdict-badge";
import type { ScoreDetail, Verdict } from "@/lib/api/types";

function getScoreColor(score: number): string {
  if (score >= 70) return "text-green-600";
  if (score >= 40) return "text-amber-600";
  return "text-red-600";
}

export function ScoreSummary({
  totalScore,
  verdict,
  scores,
}: {
  totalScore: number | null;
  verdict: Verdict | null;
  scores: ScoreDetail[] | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>종합 평가</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className={`text-4xl font-bold ${getScoreColor(totalScore ?? 0)}`}>
              {totalScore !== null ? Math.round(totalScore) : "-"}
              <span className="text-lg font-normal text-muted-foreground">점</span>
            </div>
            <VerdictBadge verdict={verdict} className="mt-1" />
          </div>
        </div>
        {scores && scores.length > 0 && <RadarChart scores={scores} />}
      </CardContent>
    </Card>
  );
}
