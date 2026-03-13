"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useBatchUpsertCompanySettings,
  useCompanySetting,
} from "@/hooks/use-settings";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const COMPANY_KEYS = [
  { key: "business_direction", label: "사업 방향", rows: 3 },
  { key: "short_term_strategy", label: "단기 전략", rows: 2 },
  { key: "mid_term_strategy", label: "중기 전략", rows: 2 },
  { key: "long_term_strategy", label: "장기 전략", rows: 2 },
  { key: "deal_criteria", label: "Deal 선정 기준", rows: 3 },
];

function useCompanySettings() {
  const queries = COMPANY_KEYS.map(({ key }) => ({
    key,
    ...useCompanySetting(key),
  }));
  const isLoading = queries.some((q) => q.isLoading);
  const serverValues: Record<string, string> = {};
  for (const q of queries) {
    serverValues[q.key] = q.data?.value ?? "";
  }
  return { serverValues, isLoading };
}

export function CompanyInfoTab() {
  const { serverValues, isLoading } = useCompanySettings();
  const batchUpsert = useBatchUpsertCompanySettings();
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!isLoading && !initialized) {
      setFormValues(serverValues);
      setInitialized(true);
    }
  }, [isLoading, initialized, serverValues]);

  const displayValues = initialized ? formValues : serverValues;

  const isDirty =
    initialized &&
    COMPANY_KEYS.some(
      ({ key }) => (formValues[key] ?? "") !== (serverValues[key] ?? ""),
    );

  function handleChange(key: string, value: string) {
    setFormValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    try {
      const items = COMPANY_KEYS.map(({ key, label }) => ({
        key,
        value: displayValues[key] ?? "",
        description: label,
      }));
      await batchUpsert.mutateAsync({ items });
      toast.success("회사 정보가 저장되었습니다");
    } catch {
      toast.error("저장에 실패했습니다");
    }
  }

  return (
    <div className="space-y-6">
      {COMPANY_KEYS.map(({ key, label, rows }) => (
        <div key={key} className="space-y-2">
          <Label>{label}</Label>
          <Textarea
            value={displayValues[key] ?? ""}
            onChange={(e) => handleChange(key, e.target.value)}
            rows={rows}
            disabled={isLoading}
            placeholder={`${label}을 입력하세요...`}
          />
        </div>
      ))}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          disabled={batchUpsert.isPending || isLoading || !isDirty}
        >
          {batchUpsert.isPending ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : null}
          저장
        </Button>
      </div>
    </div>
  );
}
