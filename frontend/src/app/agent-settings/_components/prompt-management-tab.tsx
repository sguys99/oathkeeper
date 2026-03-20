"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { usePrompts, useUpdatePrompt } from "@/hooks/use-prompts";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import type { PromptResponse } from "@/lib/api/types";
import { AgentFlowDiagram } from "./agent-flow-diagram";

const PROMPT_LABELS: Record<string, string> = {
  system: "시스템 프롬프트",
  deal_structuring: "딜 구조화",
  scoring: "스코어링",
  resource_estimation: "리소스 산정",
  risk_analysis: "리스크 분석",
  similar_project: "유사 프로젝트",
  final_verdict: "최종 판단",
};

interface FormValues {
  system_prompt: string;
  user_prompt: string;
  version: string;
  description: string;
}

function getFormValues(prompt: PromptResponse): FormValues {
  return {
    system_prompt: prompt.system_prompt,
    user_prompt: prompt.user_prompt,
    version: prompt.version,
    description: prompt.description,
  };
}

export function PromptManagementTab() {
  const { data: prompts, isLoading } = usePrompts();
  const updatePrompt = useUpdatePrompt();
  const [selectedName, setSelectedName] = useState("");
  const [formValues, setFormValues] = useState<FormValues | null>(null);
  const [initialValues, setInitialValues] = useState<FormValues | null>(null);

  const selectedPrompt = prompts?.find((p) => p.name === selectedName) ?? null;

  useEffect(() => {
    if (prompts && prompts.length > 0 && !selectedName) {
      setSelectedName("system");
    }
  }, [prompts, selectedName]);

  useEffect(() => {
    if (selectedPrompt) {
      const values = getFormValues(selectedPrompt);
      setFormValues(values);
      setInitialValues(values);
    } else {
      setFormValues(null);
      setInitialValues(null);
    }
  }, [selectedName, selectedPrompt]);

  const isDirty =
    formValues !== null &&
    initialValues !== null &&
    (formValues.system_prompt !== initialValues.system_prompt ||
      formValues.user_prompt !== initialValues.user_prompt ||
      formValues.version !== initialValues.version ||
      formValues.description !== initialValues.description);

  function handleChange<K extends keyof FormValues>(key: K, value: string) {
    setFormValues((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!selectedName || !formValues) return;
    try {
      await updatePrompt.mutateAsync({
        name: selectedName,
        data: {
          system_prompt: formValues.system_prompt,
          user_prompt: formValues.user_prompt,
          version: formValues.version,
          description: formValues.description,
        },
      });
      setInitialValues(formValues);
      toast.success("프롬프트가 저장되었습니다");
    } catch {
      toast.error("프롬프트 저장에 실패했습니다");
    }
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[3fr_2fr]">
      {/* Left: prompt editor */}
      <div className="space-y-6">
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            로딩 중...
          </div>
        )}

        <div className="grid grid-cols-3 gap-6">
          <div className="min-w-0 space-y-2">
            <Label>프롬프트 선택</Label>
            <Select value={selectedName} onValueChange={setSelectedName}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="프롬프트를 선택하세요">
                  {PROMPT_LABELS[selectedName] ?? selectedName}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {prompts?.map((p) => (
                  <SelectItem key={p.name} value={p.name}>
                    {PROMPT_LABELS[p.name] ?? p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="min-w-0 space-y-2">
            <Label>버전</Label>
            <Input
              value={formValues?.version ?? ""}
              onChange={(e) => handleChange("version", e.target.value)}
              disabled={!formValues}
            />
          </div>
          <div className="min-w-0 space-y-2">
            <Label>이름</Label>
            <Input value={selectedPrompt?.name ?? ""} disabled />
          </div>
        </div>

        {selectedPrompt && formValues && (
          <>

            <div className="space-y-2">
              <Label>설명</Label>
              <Input
                value={formValues.description}
                onChange={(e) => handleChange("description", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>System Prompt</Label>
              <Textarea
                className="font-mono text-sm"
                value={formValues.system_prompt}
                onChange={(e) => handleChange("system_prompt", e.target.value)}
                rows={12}
              />
            </div>

            <div className="space-y-2">
              <Label>User Prompt</Label>
              <Textarea
                className="font-mono text-sm"
                value={formValues.user_prompt}
                onChange={(e) => handleChange("user_prompt", e.target.value)}
                rows={12}
              />
            </div>

            {selectedPrompt.output_schema && (
              <div className="space-y-2">
                <Label>Output Schema (읽기 전용)</Label>
                <pre className="overflow-auto rounded-md border bg-muted p-4 text-sm">
                  {JSON.stringify(selectedPrompt.output_schema, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end">
              <Button
                onClick={handleSave}
                disabled={updatePrompt.isPending || !isDirty}
              >
                {updatePrompt.isPending ? (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                ) : null}
                저장
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Right: architecture diagram */}
      <div className="lg:sticky lg:top-8 lg:mt-44 lg:self-start">
        <AgentFlowDiagram selectedPrompt={selectedName} />
      </div>
    </div>
  );
}
