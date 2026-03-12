"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Info } from "lucide-react";

export function ProjectHistoryTab() {
  return (
    <div className="py-8">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>준비 중</AlertTitle>
        <AlertDescription>
          프로젝트 이력 관리 기능은 추후 업데이트에서 제공될 예정입니다.
          프로젝트 이력은 Vector DB에 저장되며, 유사 프로젝트 검색에 활용됩니다.
        </AlertDescription>
      </Alert>
    </div>
  );
}
