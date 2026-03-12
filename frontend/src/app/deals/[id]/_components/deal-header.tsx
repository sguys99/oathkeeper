"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { VerdictBadge } from "@/components/common/verdict-badge";
import type { Verdict } from "@/lib/api/types";

export function DealHeader({
  title,
  verdict,
}: {
  title: string;
  verdict: Verdict | null;
}) {
  return (
    <div className="flex items-center gap-4">
      <Link
        href="/deals"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        목록으로
      </Link>
      <h1 className="text-xl font-semibold">{title}</h1>
      <VerdictBadge verdict={verdict} className="text-sm" />
    </div>
  );
}
