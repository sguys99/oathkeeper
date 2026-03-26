"use client";

import { Fragment, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  useProjectHistory,
  useEmbedProjects,
  useDeleteEmbedding,
  usePageContent,
} from "@/hooks/use-project-history";
import { toast } from "sonner";
import { Loader2, Database, ChevronRight, ChevronDown, Trash2 } from "lucide-react";
import { formatCurrencyManWon } from "@/lib/utils";

function EmbedStatusBadge({
  isEmbedded,
  needsUpdate,
}: {
  isEmbedded: boolean;
  needsUpdate: boolean;
}) {
  if (isEmbedded && needsUpdate) {
    return (
      <Badge className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">
        업데이트 필요
      </Badge>
    );
  }
  if (isEmbedded) {
    return (
      <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
        임베딩됨
      </Badge>
    );
  }
  return <Badge variant="outline">미임베딩</Badge>;
}

function ExpandedContent({ pageId }: { pageId: string }) {
  const { data, isLoading } = usePageContent(pageId);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        로딩 중...
      </div>
    );
  }

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown>{data?.content || "페이지 내용이 없습니다"}</ReactMarkdown>
    </div>
  );
}

export function ProjectHistoryTab() {
  const { data, isLoading } = useProjectHistory();
  const embedMutation = useEmbedProjects();
  const deleteMutation = useDeleteEmbedding();
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  function toggleExpand(pageId: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(pageId)) {
        next.delete(pageId);
      } else {
        next.add(pageId);
      }
      return next;
    });
  }

  async function handleEmbed() {
    try {
      const result = await embedMutation.mutateAsync(undefined);
      toast.success(
        `임베딩 완료: ${result.embedded}개 처리, ${result.skipped}개 스킵${result.failed > 0 ? `, ${result.failed}개 실패` : ""}`,
      );
    } catch {
      toast.error("임베딩 실행에 실패했습니다");
    }
  }

  if (isLoading) {
    return (
      <div className="py-8 text-center text-muted-foreground">로딩 중...</div>
    );
  }

  const projects = data?.projects ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {data?.total ?? 0}개 프로젝트 / {data?.embedded_count ?? 0}개 임베딩
          완료
        </p>
        <Button onClick={handleEmbed} disabled={embedMutation.isPending}>
          {embedMutation.isPending ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Database className="mr-1 h-4 w-4" />
          )}
          임베딩 실행
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>프로젝트명</TableHead>
              <TableHead>업종</TableHead>
              <TableHead>기술스택</TableHead>
              <TableHead>기간(월)</TableHead>
              <TableHead>인원(계획/실제)</TableHead>
              <TableHead>계약금액</TableHead>
              <TableHead>임베딩</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {projects.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="text-center text-muted-foreground"
                >
                  노션 프로젝트 이력이 없습니다
                </TableCell>
              </TableRow>
            ) : (
              projects.map((p) => {
                const isExpanded = expandedIds.has(p.page_id);
                return (
                  <Fragment key={p.page_id}>
                    <TableRow
                      className="cursor-pointer"
                      onClick={() => toggleExpand(p.page_id)}
                    >
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-1">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                          )}
                          {p.project_name || "-"}
                        </div>
                      </TableCell>
                      <TableCell>{p.industry ?? "-"}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {p.tech_stack.map((t) => (
                            <Badge
                              key={t}
                              variant="secondary"
                              className="text-xs"
                            >
                              {t}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{p.duration_months ?? "-"}</TableCell>
                      <TableCell>
                        {p.planned_headcount ?? "-"} /{" "}
                        {p.actual_headcount ?? "-"}
                      </TableCell>
                      <TableCell>
                        {p.contract_amount != null
                          ? formatCurrencyManWon(p.contract_amount)
                          : "-"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <EmbedStatusBadge
                            isEmbedded={p.is_embedded}
                            needsUpdate={p.needs_update}
                          />
                          {p.is_embedded && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-muted-foreground hover:text-destructive"
                              disabled={deleteMutation.isPending}
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteMutation.mutate(p.page_id, {
                                  onSuccess: () =>
                                    toast.success(
                                      `${p.project_name} 임베딩이 삭제되었습니다`,
                                    ),
                                  onError: () =>
                                    toast.error("임베딩 삭제에 실패했습니다"),
                                });
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                    {isExpanded && (
                      <TableRow>
                        <TableCell
                          colSpan={7}
                          className="bg-muted/50 px-8 py-3"
                        >
                          <ExpandedContent pageId={p.page_id} />
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
