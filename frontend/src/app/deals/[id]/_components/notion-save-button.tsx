"use client";

import { Button } from "@/components/ui/button";
import { useSaveToNotion } from "@/hooks/use-notion";
import { Check, ExternalLink, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { formatDateTime } from "@/lib/utils";

export function NotionSaveButton({
  dealId,
  notionSavedAt,
}: {
  dealId: string;
  notionSavedAt: string | null;
}) {
  const saveToNotion = useSaveToNotion();

  async function handleSave() {
    try {
      const result = await saveToNotion.mutateAsync({ dealId });
      if (result.notion_page_url) {
        toast.success("Notion에 저장되었습니다", {
          action: {
            label: "열기",
            onClick: () => window.open(result.notion_page_url!, "_blank"),
          },
        });
      } else {
        toast.success("Notion에 저장되었습니다");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "저장에 실패했습니다");
    }
  }

  if (notionSavedAt) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Check className="h-4 w-4 text-green-500" />
        <span>Notion 저장 완료 ({formatDateTime(notionSavedAt)})</span>
      </div>
    );
  }

  return (
    <Button
      onClick={handleSave}
      disabled={saveToNotion.isPending}
    >
      {saveToNotion.isPending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          저장 중...
        </>
      ) : (
        <>
          <ExternalLink className="mr-2 h-4 w-4" />
          Notion에 저장
        </>
      )}
    </Button>
  );
}
