"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useDealPolling } from "@/hooks/use-deals";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const STATUS_MESSAGES: Record<string, string> = {
  pending: "분석 준비 중...",
  analyzing: "AI가 Deal을 분석하고 있습니다...",
  completed: "분석이 완료되었습니다!",
  failed: "분석 중 오류가 발생했습니다.",
};

export function AnalysisProgress({
  dealId,
  onRetry,
}: {
  dealId: string;
  onRetry: () => void;
}) {
  const router = useRouter();
  const isAnalyzing = true;
  const { data: deal } = useDealPolling(dealId, isAnalyzing);
  const status = deal?.status ?? "analyzing";

  useEffect(() => {
    if (status === "completed") {
      const timer = setTimeout(() => {
        router.push(`/deals/${dealId}`);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [status, dealId, router]);

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-4 py-12">
        {status === "analyzing" && (
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        )}
        {status === "completed" && (
          <CheckCircle2 className="h-12 w-12 text-green-500" />
        )}
        {status === "failed" && (
          <XCircle className="h-12 w-12 text-red-500" />
        )}
        <p className="text-lg font-medium">
          {STATUS_MESSAGES[status] ?? "처리 중..."}
        </p>
        {status === "analyzing" && (
          <p className="text-sm text-muted-foreground">
            평가 기준 분석, 리스크 분석, 유사 프로젝트 검색이 진행됩니다
          </p>
        )}
        {status === "failed" && (
          <Button variant="outline" onClick={onRetry}>
            다시 시도
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
