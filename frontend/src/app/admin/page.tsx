"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CompanyInfoTab } from "./_components/company-info-tab";
import { ScoringWeightsTab } from "./_components/scoring-weights-tab";
import { TeamManagementTab } from "./_components/team-management-tab";
import { CostSettingsTab } from "./_components/cost-settings-tab";
import { ProjectHistoryTab } from "./_components/project-history-tab";
import { PromptManagementTab } from "./_components/prompt-management-tab";

export default function AdminPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold">관리자 설정</h1>
      <Tabs defaultValue="company">
        <TabsList className="mb-6">
          <TabsTrigger value="company">회사 정보</TabsTrigger>
          <TabsTrigger value="weights">평가 기준</TabsTrigger>
          <TabsTrigger value="team">인력 관리</TabsTrigger>
          <TabsTrigger value="cost">비용 설정</TabsTrigger>
          <TabsTrigger value="history">프로젝트 이력</TabsTrigger>
          <TabsTrigger value="prompts">프롬프트 관리</TabsTrigger>
        </TabsList>
        <TabsContent value="company">
          <CompanyInfoTab />
        </TabsContent>
        <TabsContent value="weights">
          <ScoringWeightsTab />
        </TabsContent>
        <TabsContent value="team">
          <TeamManagementTab />
        </TabsContent>
        <TabsContent value="cost">
          <CostSettingsTab />
        </TabsContent>
        <TabsContent value="history">
          <ProjectHistoryTab />
        </TabsContent>
        <TabsContent value="prompts">
          <PromptManagementTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
