import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskIndicator } from "@/components/common/risk-indicator";
import type { RiskItem, RiskInterdependency } from "@/lib/api/types";

interface RiskListProps {
  risks: RiskItem[];
  interdependencies?: RiskInterdependency[] | null;
}

export function RiskList({ risks, interdependencies }: RiskListProps) {
  const grouped = risks.reduce(
    (acc, risk) => {
      const cat = risk.category;
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(risk);
      return acc;
    },
    {} as Record<string, RiskItem[]>,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>리스크 분석</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {Object.entries(grouped).map(([category, items]) => (
          <div key={category}>
            <h4 className="mb-2 text-sm font-medium">{category}</h4>
            <div className="space-y-3">
              {items.map((risk, idx) => (
                <div
                  key={idx}
                  className="rounded-md border p-3 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{risk.item}</span>
                    <div className="flex items-center gap-2">
                      {risk.probability && risk.impact && (
                        <span className="text-[10px] text-muted-foreground">
                          확률 {risk.probability} / 영향 {risk.impact}
                        </span>
                      )}
                      <RiskIndicator level={risk.level} />
                    </div>
                  </div>
                  {risk.evidence && (
                    <p className="text-xs text-orange-600">
                      근거: {risk.evidence}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {risk.description}
                  </p>
                  {risk.mitigation && (
                    <p className="text-xs text-blue-600">
                      완화 방안: {risk.mitigation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        {interdependencies && interdependencies.length > 0 && (
          <div>
            <h4 className="mb-2 text-sm font-medium">리스크 상호작용</h4>
            <div className="space-y-3">
              {interdependencies.map((item, idx) => (
                <div key={idx} className="rounded-md border border-dashed border-orange-300 bg-orange-50 p-3 space-y-1">
                  <span className="text-sm font-medium">
                    {item.risk_pair.join(" + ")}
                  </span>
                  <p className="text-xs text-muted-foreground">
                    {item.combined_effect}
                  </p>
                  <p className="text-xs text-orange-600">
                    증폭 효과: {item.amplification}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
