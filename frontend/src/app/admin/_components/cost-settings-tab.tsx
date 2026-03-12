"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUpsertCompanySetting, useCompanySetting } from "@/hooks/use-settings";
import { toast } from "sonner";
import { Plus, Loader2 } from "lucide-react";

const COST_KEYS = [
  { key: "cost_hw_server", label: "HW 서버 비용" },
  { key: "cost_sw_license", label: "SW 라이선스 비용" },
  { key: "cost_cloud_infra", label: "클라우드 인프라 비용" },
  { key: "cost_etc", label: "기타 비용" },
];

function CostField({ settingKey, label }: { settingKey: string; label: string }) {
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
    <div className="flex items-end gap-2">
      <div className="flex-1 space-y-1">
        <Label className="text-sm">{label}</Label>
        <Input
          value={displayValue}
          onChange={(e) => setValue(e.target.value)}
          placeholder="비용 또는 설명 입력"
          disabled={isLoading}
        />
      </div>
      <Button
        size="sm"
        onClick={handleSave}
        disabled={upsert.isPending || isLoading}
      >
        {upsert.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : "저장"}
      </Button>
    </div>
  );
}

export function CostSettingsTab() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        프로젝트 비용 산정에 사용되는 항목별 비용을 설정합니다.
      </p>
      {COST_KEYS.map(({ key, label }) => (
        <CostField key={key} settingKey={key} label={label} />
      ))}
    </div>
  );
}
