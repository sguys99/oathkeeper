"use client";

import { use } from "react";
import Link from "next/link";
import { useDeal } from "@/hooks/use-deals";
import { useAgentLogTree } from "@/hooks/use-agent-logs";
import { LogTimeline } from "./_components/log-timeline";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function DealLogsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: deal, isLoading: dealLoading } = useDeal(id);
  const { data: tree, isLoading: logsLoading } = useAgentLogTree(id);

  if (dealLoading || logsLoading) {
    return (
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 text-center">
        <p className="text-muted-foreground">Deal을 찾을 수 없습니다</p>
        <Link href="/deals">
          <Button variant="outline" className="mt-4">
            목록으로 돌아가기
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href={`/deals/${id}`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            분석 결과로 돌아가기
          </Link>
          <h1 className="text-2xl font-semibold">에이전트 로그</h1>
          <p className="mt-1 text-sm text-muted-foreground">{deal.title}</p>
        </div>
      </div>

      {tree && tree.logs.length > 0 ? (
        <LogTimeline tree={tree} />
      ) : (
        <div className="rounded-md border p-8 text-center text-muted-foreground">
          이 Deal에 대한 에이전트 로그가 없습니다
        </div>
      )}
    </div>
  );
}
