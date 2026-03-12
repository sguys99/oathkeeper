import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskIndicator } from "@/components/common/risk-indicator";
import type { RiskItem } from "@/lib/api/types";

export function RiskList({ risks }: { risks: RiskItem[] }) {
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
                    <RiskIndicator level={risk.level} />
                  </div>
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
      </CardContent>
    </Card>
  );
}
