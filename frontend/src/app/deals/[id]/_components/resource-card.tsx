import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Clock, Banknote, TrendingUp } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { ResourceEstimate } from "@/lib/api/types";

export function ResourceCard({
  resource,
}: {
  resource: ResourceEstimate;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>소요 리소스</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {resource.team_composition && (
            <div className="flex items-start gap-3">
              <Users className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">팀 구성</p>
                <p className="text-sm font-medium">
                  {resource.team_composition
                    .map((t) => `${t.role} ${t.count}명`)
                    .join(", ")}
                </p>
              </div>
            </div>
          )}
          {resource.duration_months != null && (
            <div className="flex items-start gap-3">
              <Clock className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">예상 기간</p>
                <p className="text-sm font-medium">
                  {resource.duration_months}개월
                </p>
              </div>
            </div>
          )}
          {resource.total_cost != null && (
            <div className="flex items-start gap-3">
              <Banknote className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">총 비용</p>
                <p className="text-sm font-medium">
                  {formatCurrency(resource.total_cost)}
                </p>
              </div>
            </div>
          )}
          {resource.expected_margin != null && (
            <div className="flex items-start gap-3">
              <TrendingUp className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">예상 마진</p>
                <p className="text-sm font-medium">
                  {Math.round(resource.expected_margin * 100)}%
                </p>
              </div>
            </div>
          )}
        </div>
        {resource.rationale && (
          <p className="mt-4 text-sm text-muted-foreground">
            {resource.rationale}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
