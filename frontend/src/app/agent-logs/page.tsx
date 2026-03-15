"use client";

import Link from "next/link";
import { useDeals } from "@/hooks/use-deals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText } from "lucide-react";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

const VERDICT_LABELS: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  go: { label: "Go", variant: "default" },
  conditional_go: { label: "Conditional Go", variant: "secondary" },
  no_go: { label: "No-Go", variant: "destructive" },
  pending: { label: "보류", variant: "outline" },
};

export default function AgentLogsPage() {
  const { data, isLoading } = useDeals({ limit: 50 });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-8">
        <h1 className="text-2xl font-semibold">에이전트 로그</h1>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16" />
        ))}
      </div>
    );
  }

  const deals = data?.items ?? [];
  const analyzedDeals = deals.filter(
    (d) => d.status === "completed" || d.status === "failed",
  );

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">에이전트 로그</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          각 Deal의 분석 과정에서 에이전트가 사용한 프롬프트와 출력을 확인합니다
        </p>
      </div>

      {analyzedDeals.length === 0 ? (
        <div className="rounded-md border p-8 text-center text-muted-foreground">
          분석이 완료된 Deal이 없습니다
        </div>
      ) : (
        <div className="space-y-3">
          {analyzedDeals.map((deal) => {
            const verdictKey = (deal.structured_data as Record<string, unknown> | null)?.verdict as string | undefined;
            const verdictInfo = verdictKey ? VERDICT_LABELS[verdictKey] ?? null : null;

            return (
              <Card key={deal.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{deal.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(deal.created_at), "yyyy-MM-dd HH:mm", {
                          locale: ko,
                        })}
                        {deal.creator && ` · ${deal.creator.name}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        deal.status === "completed" ? "secondary" : "destructive"
                      }
                    >
                      {deal.status === "completed" ? "완료" : "실패"}
                    </Badge>
                    {verdictInfo && (
                      <Badge variant={verdictInfo.variant}>
                        {verdictInfo.label}
                      </Badge>
                    )}
                    <Link href={`/deals/${deal.id}/logs`}>
                      <Button variant="outline" size="sm">
                        로그 보기
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
