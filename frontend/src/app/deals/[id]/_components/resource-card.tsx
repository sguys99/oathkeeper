import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Users,
  Clock,
  Banknote,
  TrendingUp,
  Package,
  CalendarRange,
  ShieldAlert,
} from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { ResourceEstimate } from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";

function getMarginColor(margin: number) {
  if (margin >= 0.2) return "text-green-600";
  if (margin >= 0.1) return "text-yellow-600";
  return "text-red-600";
}

export function ResourceCard({
  resource,
}: {
  resource: ResourceEstimate;
}) {
  const totalCost =
    resource.cost_breakdown?.total_cost ?? resource.total_cost;
  const margin =
    resource.profitability?.expected_margin ?? resource.expected_margin;

  return (
    <Card>
      <CardHeader>
        <CardTitle>소요 리소스</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {resource.team_composition && (
            <div className="flex items-start gap-3">
              <Users className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">팀 구성</p>
                <p className="text-sm font-medium">
                  {resource.team_composition
                    .map(
                      (t) =>
                        `${t.role} ${t.count}명${t.duration_months ? `(${t.duration_months}개월)` : ""}`,
                    )
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
                  {resource.duration_with_buffer != null && (
                    <span className="text-xs text-muted-foreground">
                      {" "}
                      (버퍼 포함 {resource.duration_with_buffer}개월)
                    </span>
                  )}
                </p>
              </div>
            </div>
          )}
          {totalCost != null && (
            <div className="flex items-start gap-3">
              <Banknote className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">총 비용</p>
                <p className="text-sm font-medium">
                  {formatCurrency(totalCost)}
                </p>
                {resource.cost_breakdown && (
                  <p className="text-xs text-muted-foreground">
                    인건비 {formatCurrency(resource.cost_breakdown.labor_cost)}{" "}
                    + 기타 {formatCurrency(resource.cost_breakdown.overhead_cost)}
                  </p>
                )}
              </div>
            </div>
          )}
          {margin != null && (
            <div className="flex items-start gap-3">
              <TrendingUp className="mt-0.5 h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">예상 마진</p>
                <p className={`text-sm font-medium ${getMarginColor(margin)}`}>
                  {Math.round(margin * 100)}%
                </p>
                {resource.profitability?.margin_assessment && (
                  <p className="text-xs text-muted-foreground">
                    {resource.profitability.margin_assessment}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Work Breakdown */}
        {resource.work_breakdown && resource.work_breakdown.length > 0 && (
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Package className="h-4 w-4 text-muted-foreground" />
              <h4 className="text-sm font-semibold">작업 영역 분석</h4>
            </div>
            <div className="space-y-2">
              {resource.work_breakdown.map((w, i) => (
                <div
                  key={i}
                  className="flex items-start justify-between rounded-md border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{w.area}</span>
                      {w.is_reusable ? (
                        <Badge variant="secondary">
                          재활용 {Math.round(w.reuse_ratio * 100)}%
                        </Badge>
                      ) : (
                        <Badge variant="outline">신규 개발</Badge>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {w.description}
                    </p>
                  </div>
                  <div className="ml-4 text-right">
                    <p className="text-sm font-medium">
                      {w.effort_person_months}인·월
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Phases */}
        {resource.phases && resource.phases.length > 0 && (
          <div>
            <div className="mb-2 flex items-center gap-2">
              <CalendarRange className="h-4 w-4 text-muted-foreground" />
              <h4 className="text-sm font-semibold">프로젝트 페이즈</h4>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {resource.phases.map((p, i) => (
                <div key={i} className="rounded-md border p-3">
                  <p className="text-sm font-medium">{p.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {p.duration_months}개월 · {p.roles_needed.join(", ")}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risk Buffer */}
        {resource.risk_buffer_ratio != null && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ShieldAlert className="h-4 w-4" />
            <span>
              리스크 버퍼: {Math.round(resource.risk_buffer_ratio * 100)}%
            </span>
          </div>
        )}

        {/* Cost Calculation Detail */}
        {resource.cost_breakdown?.cost_calculation && (
          <div className="rounded-md bg-muted/50 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              비용 산출 근거
            </p>
            <p className="mt-1 text-sm">
              {resource.cost_breakdown.cost_calculation}
            </p>
          </div>
        )}

        {/* Rationale */}
        {resource.rationale && (
          <p className="text-sm text-muted-foreground">{resource.rationale}</p>
        )}
      </CardContent>
    </Card>
  );
}
