"use client";

import { use } from "react";
import Link from "next/link";
import { useDeal } from "@/hooks/use-deals";
import { useAnalysis } from "@/hooks/use-analysis";
import { DealHeader } from "./_components/deal-header";
import { ScoreSummary } from "./_components/score-summary";
import { DealOverviewSidebar } from "./_components/deal-overview-sidebar";
import { CriteriaScores } from "./_components/criteria-scores";
import { ResourceCard } from "./_components/resource-card";
import { RiskList } from "./_components/risk-list";
import { SimilarProjects } from "./_components/similar-projects";
import { Recommendations } from "./_components/recommendations";
import { NotionSaveButton } from "./_components/notion-save-button";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { Verdict } from "@/lib/api/types";

export default function DealDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: deal, isLoading: dealLoading } = useDeal(id);
  const { data: analysis, isLoading: analysisLoading } = useAnalysis(id);

  if (dealLoading || analysisLoading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-8">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 text-center">
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
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8">
      <DealHeader
        title={deal.title}
        verdict={(analysis?.verdict as Verdict) ?? null}
      />

      {analysis ? (
        <>
          <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
            <ScoreSummary
              totalScore={analysis.total_score}
              verdict={(analysis.verdict as Verdict) ?? null}
              scores={analysis.scores}
            />
            <DealOverviewSidebar structuredData={deal.structured_data} />
          </div>

          {analysis.scores && analysis.scores.length > 0 && (
            <CriteriaScores scores={analysis.scores} />
          )}

          {analysis.resource_estimate && (
            <ResourceCard resource={analysis.resource_estimate} />
          )}

          {analysis.risks && analysis.risks.length > 0 && (
            <RiskList risks={analysis.risks} interdependencies={analysis.risk_interdependencies} />
          )}

          {analysis.similar_projects &&
            analysis.similar_projects.length > 0 && (
              <SimilarProjects projects={analysis.similar_projects} />
            )}

          {analysis.report_markdown && (
            <Recommendations markdown={analysis.report_markdown} />
          )}

          <div className="flex items-center justify-between border-t pt-6">
            <div className="flex items-center gap-3">
              <NotionSaveButton
                dealId={deal.id}
                notionSavedAt={analysis.notion_saved_at}
              />
              <Link href={`/deals/${id}/logs`}>
                <Button variant="outline">로그 보기</Button>
              </Link>
            </div>
            <Link href="/deals">
              <Button variant="outline">닫기</Button>
            </Link>
          </div>
        </>
      ) : (
        <div className="rounded-md border p-8 text-center text-muted-foreground">
          아직 분석 결과가 없습니다
        </div>
      )}
    </div>
  );
}
