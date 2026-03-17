import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

export function DealOverviewSidebar({
  structuredData,
}: {
  structuredData: Record<string, unknown> | null;
}) {
  if (!structuredData) return null;

  const fields: { label: string; key: string; format?: (v: unknown) => string }[] = [
    { label: "고객사", key: "customer_name" },
    { label: "고객 규모", key: "customer_size" },
    { label: "산업", key: "customer_industry" },
    {
      label: "계약 금액",
      key: "expected_amount",
      format: (v) => formatCurrency(v as number),
    },
    {
      label: "수행 기간",
      key: "duration_months",
      format: (v) => `${v}개월`,
    },
    { label: "결제 조건", key: "payment_terms" },
  ];

  const techReqs = structuredData.tech_requirements as string[] | undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deal 개요</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {fields.map(({ label, key, format }) => {
          const value = structuredData[key];
          if (value === null || value === undefined) return null;
          return (
            <div key={key}>
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="text-sm font-medium">
                {format ? format(value) : String(value)}
              </dd>
            </div>
          );
        })}
        {techReqs && techReqs.length > 0 && (
          <div>
            <dt className="text-xs text-muted-foreground">기술 스택</dt>
            <dd className="mt-1 flex flex-wrap gap-1">
              {techReqs.map((tech) => (
                <Badge key={tech} variant="secondary" className="text-xs">
                  {tech}
                </Badge>
              ))}
            </dd>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
