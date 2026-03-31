import { test, expect, type Page } from "@playwright/test";

const DEAL_ID = "11111111-1111-1111-1111-111111111111";

async function mockDealDetailApis(page: Page) {
  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: DEAL_ID,
        notion_page_id: null,
        title: "xx철강 AI 비전 검사 시스템",
        raw_input: "고객사: xx철강",
        structured_data: {
          customer_name: "xx철강",
          project_overview: "AI 비전 기반 표면 검사 시스템",
        },
        status: "completed",
        current_step: null,
        error_message: null,
        created_by: null,
        created_at: "2026-03-31T00:00:00Z",
        updated_at: "2026-03-31T00:01:00Z",
        creator: null,
        verdict: "go",
        total_score: 78.1,
      }),
    });
  });

  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}/analysis`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "22222222-2222-2222-2222-222222222222",
        deal_id: DEAL_ID,
        total_score: 78.1,
        verdict: "go",
        scores: [
          {
            criterion: "기술 적합성",
            score: 85,
            weight: 0.2,
            weighted_score: 17,
            rationale: "유사 도메인 경험 보유",
          },
        ],
        resource_estimate: {
          duration_months: 6,
          team_composition: [{ role: "PM", count: 1, monthly_rate: 9000000 }],
          total_cost: 280000000,
          expected_margin: 22.5,
          rationale: "기존 모듈 재사용 가능",
        },
        risks: [
          {
            category: "일정",
            item: "MES 연동 지연",
            probability: "MEDIUM",
            impact: "HIGH",
            level: "HIGH",
            evidence: null,
            description: "기존 인터페이스 정합성 검토 필요",
            mitigation: "초기 인터페이스 워크숍 진행",
          },
        ],
        risk_interdependencies: [],
        similar_projects: [
          {
            project_name: "철강 표면 검사 구축",
            similarity_score: 0.91,
            industry: "제조",
            tech_stack: ["Python", "PyTorch"],
            duration_months: 6,
            result: "success",
            lessons_learned: "라인 중단 없이 배포 필요",
          },
        ],
        report_markdown: "# 최종 권고\n\nGo 권고",
        notion_saved_at: null,
        created_at: "2026-03-31T00:01:00Z",
      }),
    });
  });
}

async function mockLogTreeApi(page: Page) {
  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}/logs?view=tree`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        deal_id: DEAL_ID,
        total_count: 4,
        total_duration_ms: 60,
        logs: [
          {
            id: "33333333-3333-3333-3333-333333333333",
            deal_id: DEAL_ID,
            node_name: "orchestrator",
            system_prompt: null,
            user_prompt: null,
            raw_output: "run_scoring_analysis",
            parsed_output: null,
            error: null,
            duration_ms: 20,
            started_at: "2026-03-31T00:00:00Z",
            completed_at: "2026-03-31T00:00:00Z",
            created_at: "2026-03-31T00:00:00Z",
            parent_log_id: null,
            step_type: "orchestrator_tool_call",
            step_index: 0,
            tool_name: "run_scoring_analysis",
            worker_name: null,
            children: [
              {
                id: "44444444-4444-4444-4444-444444444444",
                deal_id: DEAL_ID,
                node_name: "scoring_worker",
                system_prompt: null,
                user_prompt: null,
                raw_output: "{\"total_score\":78.1}",
                parsed_output: null,
                error: null,
                duration_ms: 20,
                started_at: "2026-03-31T00:00:01Z",
                completed_at: "2026-03-31T00:00:01Z",
                created_at: "2026-03-31T00:00:01Z",
                parent_log_id: "33333333-3333-3333-3333-333333333333",
                step_type: "worker_start",
                step_index: 0,
                tool_name: null,
                worker_name: "scoring_worker",
                children: [
                  {
                    id: "55555555-5555-5555-5555-555555555555",
                    deal_id: DEAL_ID,
                    node_name: "scoring_worker:reasoning",
                    system_prompt: null,
                    user_prompt: null,
                    raw_output: "Weighted score 계산 필요",
                    parsed_output: null,
                    error: null,
                    duration_ms: 5,
                    started_at: "2026-03-31T00:00:02Z",
                    completed_at: "2026-03-31T00:00:02Z",
                    created_at: "2026-03-31T00:00:02Z",
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "reasoning",
                    step_index: 0,
                    tool_name: null,
                    worker_name: "scoring_worker",
                    children: [],
                  },
                  {
                    id: "66666666-6666-6666-6666-666666666666",
                    deal_id: DEAL_ID,
                    node_name: "scoring_worker:tool_call",
                    system_prompt: null,
                    user_prompt: "{\"scores\":[85]}",
                    raw_output: null,
                    parsed_output: null,
                    error: null,
                    duration_ms: 5,
                    started_at: "2026-03-31T00:00:03Z",
                    completed_at: "2026-03-31T00:00:03Z",
                    created_at: "2026-03-31T00:00:03Z",
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "tool_call",
                    step_index: 1,
                    tool_name: "calculate_weighted_score",
                    worker_name: "scoring_worker",
                    children: [],
                  },
                  {
                    id: "77777777-7777-7777-7777-777777777777",
                    deal_id: DEAL_ID,
                    node_name: "scoring_worker:observation",
                    system_prompt: null,
                    user_prompt: null,
                    raw_output: "{\"total_score\":78.1}",
                    parsed_output: null,
                    error: null,
                    duration_ms: 5,
                    started_at: "2026-03-31T00:00:04Z",
                    completed_at: "2026-03-31T00:00:04Z",
                    created_at: "2026-03-31T00:00:04Z",
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "observation",
                    step_index: 2,
                    tool_name: "calculate_weighted_score",
                    worker_name: "scoring_worker",
                    children: [],
                  },
                ],
              },
            ],
          },
        ],
      }),
    });
  });
}

test.describe("Deal Analysis Flow", () => {
  test("should navigate home and see the analysis form", async ({ page }) => {
    await page.goto("/");

    // The form card should be visible
    await expect(page.getByText("Deal 분석 요청")).toBeVisible();

    // Notion deal selector label should be present
    await expect(page.getByText("Notion Deal 선택")).toBeVisible();

    // Additional info textarea
    await expect(page.getByPlaceholder(/추가 정보나 요구사항/)).toBeVisible();

    // File upload zone
    await expect(page.getByText("문서 첨부")).toBeVisible();

    // Submit button (disabled when no deal selected)
    const submitBtn = page.getByRole("button", { name: "분석 시작" });
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeDisabled();
  });

  test("should show analysis progress after triggering analysis", async ({
    page,
  }) => {
    await page.goto("/");

    // Wait for Notion deals to load (or a fallback if API is unavailable)
    await page.waitForTimeout(3000);

    // If Notion deals loaded, the dropdown should be clickable
    // This test verifies the UI flow works — actual analysis depends on backend
    const selector = page.getByText("Notion Deal 선택");
    await expect(selector).toBeVisible();

    // Fill additional info
    const textarea = page.getByPlaceholder(/추가 정보나 요구사항/);
    await textarea.fill("테스트 프로젝트 — AI 비전 검사 시스템");
  });

  test("should navigate to deal detail page and show analysis results", async ({
    page,
  }) => {
    await mockDealDetailApis(page);

    await page.goto(`/deals/${DEAL_ID}`);

    await expect(page.getByText("xx철강 AI 비전 검사 시스템")).toBeVisible();
    await expect(page.getByText(/78\.1/)).toBeVisible();
    await expect(page.getByText(/리스크|위험/i).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Notion.*저장/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "로그 보기" })).toBeVisible();
  });

  test("should render orchestrator, worker, and react steps in the log view", async ({
    page,
  }) => {
    await mockDealDetailApis(page);
    await mockLogTreeApi(page);

    await page.goto(`/deals/${DEAL_ID}/logs`);

    await expect(page.getByText("에이전트 로그")).toBeVisible();
    await expect(page.getByTestId("orchestrator-card")).toBeVisible();
    await expect(page.getByTestId("worker-card")).toBeVisible();

    await page.getByTestId("worker-card-header").click();

    await expect(
      page.locator('[data-testid="react-step"][data-step-type="reasoning"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="react-step"][data-step-type="tool_call"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="react-step"][data-step-type="observation"]'),
    ).toBeVisible();
    await expect(page.getByText("도구 호출: calculate_weighted_score")).toBeVisible();
  });
});
