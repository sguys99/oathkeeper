"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { VerdictBadge } from "@/components/common/verdict-badge";
import { EmptyState } from "@/components/common/empty-state";
import { useDeals } from "@/hooks/use-deals";
import { DealFilters } from "./deal-filters";
import { Pagination } from "./pagination";
import { formatDate } from "@/lib/utils";
import type { Verdict } from "@/lib/api/types";

const LIMIT = 20;

export function DealTable() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [offset, setOffset] = useState(0);

  const { data, isLoading } = useDeals({
    status: statusFilter === "all" ? undefined : statusFilter,
    offset,
    limit: LIMIT,
  });

  const filteredItems = data?.items.filter((deal) =>
    search ? deal.title.toLowerCase().includes(search.toLowerCase()) : true,
  );

  return (
    <div className="space-y-4">
      <DealFilters
        search={search}
        onSearchChange={(v) => {
          setSearch(v);
          setOffset(0);
        }}
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => {
          setStatusFilter(v);
          setOffset(0);
        }}
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : filteredItems && filteredItems.length > 0 ? (
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>고객사 / Deal</TableHead>
                <TableHead className="w-[100px]">판단</TableHead>
                <TableHead className="w-[80px]">점수</TableHead>
                <TableHead className="w-[120px]">생성일</TableHead>
                <TableHead className="w-[100px]">담당자</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((deal) => (
                <TableRow
                  key={deal.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/deals/${deal.id}`)}
                >
                  <TableCell className="font-medium">{deal.title}</TableCell>
                  <TableCell>
                    <VerdictBadge
                      verdict={
                        deal.status === "completed"
                          ? ((deal.structured_data as Record<string, unknown>)
                              ?.verdict as Verdict) ?? null
                          : null
                      }
                    />
                  </TableCell>
                  <TableCell>
                    {deal.status === "completed" ? "-" : "-"}
                  </TableCell>
                  <TableCell>{formatDate(deal.created_at)}</TableCell>
                  <TableCell>
                    {deal.creator?.name ?? "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <EmptyState message="Deal이 없습니다" />
      )}

      {data && (
        <Pagination
          offset={offset}
          limit={LIMIT}
          total={data.total}
          onPageChange={setOffset}
        />
      )}
    </div>
  );
}
