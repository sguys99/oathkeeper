import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { DealTable } from "./_components/deal-table";

export default function DealsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Deal 현황</h1>
        <Link href="/">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            새 분석
          </Button>
        </Link>
      </div>
      <DealTable />
    </div>
  );
}
