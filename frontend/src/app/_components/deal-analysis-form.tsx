"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { NotionDealSelector } from "./notion-deal-selector";
import { FileUploadZone } from "./file-upload-zone";
import { AnalysisProgress } from "./analysis-progress";
import { useNotionDeals } from "@/hooks/use-notion";
import { useCreateDeal, useImportedNotionPageIds, useUploadDocument } from "@/hooks/use-deals";
import { useTriggerAnalysis } from "@/hooks/use-analysis";
import { useCurrentUser } from "@/hooks/use-current-user";
import { ApiError } from "@/lib/api/client";
import type { NotionDeal } from "@/lib/api/types";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export function DealAnalysisForm() {
  const [selectedDeal, setSelectedDeal] = useState<NotionDeal | null>(null);
  const [additionalInfo, setAdditionalInfo] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [analyzingDealId, setAnalyzingDealId] = useState<string | null>(null);

  const router = useRouter();
  const { data: currentUser } = useCurrentUser();
  const { data: notionData, isLoading: notionLoading } = useNotionDeals();
  const { data: importedIds } = useImportedNotionPageIds();
  const createDeal = useCreateDeal();
  const uploadDoc = useUploadDocument();
  const triggerAnalysis = useTriggerAnalysis();

  const importedPageIds = new Set(importedIds ?? []);

  const isSubmitting =
    createDeal.isPending || uploadDoc.isPending || triggerAnalysis.isPending;

  async function handleSubmit() {
    if (!selectedDeal) {
      toast.error("Notion Deal을 선택해주세요");
      return;
    }

    try {
      // 1. Create deal
      const deal = await createDeal.mutateAsync({
        title: selectedDeal.deal_info,
        raw_input: additionalInfo || null,
        notion_page_id: selectedDeal.page_id,
        created_by: currentUser?.id ?? null,
      });

      // 2. Upload file if provided
      if (file) {
        await uploadDoc.mutateAsync({ dealId: deal.id, file });
      }

      // 3. Trigger analysis
      await triggerAnalysis.mutateAsync(deal.id);

      setAnalyzingDealId(deal.id);
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.status === 409 &&
        err.body?.existing_deal_id
      ) {
        toast.error("이미 분석된 Deal입니다", {
          action: {
            label: "결과 보기",
            onClick: () =>
              router.push(`/deals/${err.body.existing_deal_id}`),
          },
        });
      } else {
        toast.error(err instanceof Error ? err.message : "오류가 발생했습니다");
      }
    }
  }

  function handleRetry() {
    setAnalyzingDealId(null);
    setSelectedDeal(null);
    setAdditionalInfo("");
    setFile(null);
  }

  if (analyzingDealId) {
    return <AnalysisProgress dealId={analyzingDealId} onRetry={handleRetry} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deal 분석 요청</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label>Notion Deal 선택</Label>
          <NotionDealSelector
            deals={notionData?.deals ?? []}
            value={selectedDeal}
            onSelect={setSelectedDeal}
            disabled={notionLoading || isSubmitting}
            importedPageIds={importedPageIds}
          />
          {notionLoading && (
            <p className="text-xs text-muted-foreground">
              Notion에서 Deal 목록을 불러오는 중...
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="additional-info">추가 정보 (선택)</Label>
          <Textarea
            id="additional-info"
            placeholder="Deal에 대한 추가 정보나 요구사항을 입력하세요..."
            value={additionalInfo}
            onChange={(e) => setAdditionalInfo(e.target.value)}
            rows={4}
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-2">
          <Label>문서 첨부 (선택)</Label>
          <FileUploadZone
            file={file}
            onFileChange={setFile}
            disabled={isSubmitting}
          />
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!selectedDeal || isSubmitting}
          className="w-full"
          size="lg"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              처리 중...
            </>
          ) : (
            "분석 시작"
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
