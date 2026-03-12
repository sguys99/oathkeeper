"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCompanySetting, useUpsertCompanySetting } from "@/hooks/use-settings";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const COMPANY_KEYS = [
  { key: "business_direction", label: "사업 방향", rows: 3 },
  { key: "short_term_strategy", label: "단기 전략", rows: 2 },
  { key: "mid_term_strategy", label: "중기 전략", rows: 2 },
  { key: "long_term_strategy", label: "장기 전략", rows: 2 },
  { key: "deal_criteria", label: "Deal 선정 기준", rows: 3 },
];

function SettingField({
  settingKey,
  label,
  rows,
}: {
  settingKey: string;
  label: string;
  rows: number;
}) {
  const { data, isLoading } = useCompanySetting(settingKey);
  const upsert = useUpsertCompanySetting();
  const [value, setValue] = useState<string | null>(null);

  const displayValue = value ?? data?.value ?? "";

  async function handleSave() {
    try {
      await upsert.mutateAsync({
        key: settingKey,
        value: displayValue,
        description: label,
      });
      toast.success(`${label} 저장 완료`);
    } catch {
      toast.error("저장에 실패했습니다");
    }
  }

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Textarea
        value={displayValue}
        onChange={(e) => setValue(e.target.value)}
        rows={rows}
        disabled={isLoading}
        placeholder={`${label}을 입력하세요...`}
      />
      <div className="flex justify-end">
        <Button
          size="sm"
          onClick={handleSave}
          disabled={upsert.isPending || isLoading}
        >
          {upsert.isPending ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : null}
          저장
        </Button>
      </div>
    </div>
  );
}

export function CompanyInfoTab() {
  return (
    <div className="space-y-6">
      {COMPANY_KEYS.map(({ key, label, rows }) => (
        <SettingField key={key} settingKey={key} label={label} rows={rows} />
      ))}
    </div>
  );
}
