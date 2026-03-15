"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PromptManagementTab } from "./_components/prompt-management-tab";

export default function AgentSettingsPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">에이전트 설정</h1>
      <Tabs defaultValue="prompts">
        <TabsList className="mb-6">
          <TabsTrigger value="prompts">프롬프트 관리</TabsTrigger>
        </TabsList>
        <TabsContent value="prompts">
          <PromptManagementTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
