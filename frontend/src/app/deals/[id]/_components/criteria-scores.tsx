import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreBar } from "@/components/common/score-bar";
import type { ScoreDetail } from "@/lib/api/types";

export function CriteriaScores({ scores }: { scores: ScoreDetail[] }) {
  const sorted = [...scores].sort(
    (a, b) => b.weighted_score - a.weighted_score,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>평가 기준별 점수</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {sorted.map((s) => (
          <div key={s.criterion} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{s.criterion}</span>
              <span className="text-muted-foreground">
                가중치 {Math.round(s.weight * 100)}%
              </span>
            </div>
            <ScoreBar score={s.score} />
            {s.rationale && (
              <p className="text-xs text-muted-foreground">{s.rationale}</p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
