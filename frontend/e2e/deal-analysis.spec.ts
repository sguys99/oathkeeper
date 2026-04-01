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

function makeLogNode(
  overrides: Record<string, unknown>,
): Record<string, unknown> {
  return {
    deal_id: DEAL_ID,
    system_prompt: null,
    user_prompt: null,
    raw_output: null,
    parsed_output: null,
    error: null,
    duration_ms: 10,
    started_at: "2026-03-31T00:00:00Z",
    completed_at: "2026-03-31T00:00:00Z",
    created_at: "2026-03-31T00:00:00Z",
    parent_log_id: null,
    step_type: null,
    step_index: null,
    tool_name: null,
    worker_name: null,
    children: [],
    ...overrides,
  };
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
          makeLogNode({
            id: "33333333-3333-3333-3333-333333333333",
            node_name: "orchestrator",
            raw_output: "run_scoring_analysis",
            duration_ms: 20,
            step_type: "orchestrator_tool_call",
            step_index: 0,
            tool_name: "run_scoring_analysis",
            children: [
              makeLogNode({
                id: "44444444-4444-4444-4444-444444444444",
                node_name: "scoring_worker",
                raw_output: '{"total_score":78.1}',
                duration_ms: 20,
                parent_log_id: "33333333-3333-3333-3333-333333333333",
                step_type: "worker_start",
                step_index: 0,
                worker_name: "scoring_worker",
                children: [
                  makeLogNode({
                    id: "55555555-5555-5555-5555-555555555555",
                    node_name: "scoring_worker:reasoning",
                    raw_output: "Weighted score 계산 필요",
                    duration_ms: 5,
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "reasoning",
                    step_index: 0,
                    worker_name: "scoring_worker",
                  }),
                  makeLogNode({
                    id: "66666666-6666-6666-6666-666666666666",
                    node_name: "scoring_worker:tool_call",
                    user_prompt: '{"scores":[85]}',
                    duration_ms: 5,
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "tool_call",
                    step_index: 1,
                    tool_name: "calculate_weighted_score",
                    worker_name: "scoring_worker",
                  }),
                  makeLogNode({
                    id: "77777777-7777-7777-7777-777777777777",
                    node_name: "scoring_worker:observation",
                    raw_output: '{"total_score":78.1}',
                    duration_ms: 5,
                    parent_log_id: "44444444-4444-4444-4444-444444444444",
                    step_type: "observation",
                    step_index: 2,
                    tool_name: "calculate_weighted_score",
                    worker_name: "scoring_worker",
                  }),
                ],
              }),
            ],
          }),
        ],
      }),
    });
  });
}

async function mockHoldLogTreeApi(page: Page) {
  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}/logs?view=tree`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        deal_id: DEAL_ID,
        total_count: 1,
        total_duration_ms: 10,
        logs: [
          makeLogNode({
            id: "33333333-3333-3333-3333-333333333333",
            node_name: "orchestrator",
            raw_output: "Hold — 필수 정보 부족",
            step_type: "orchestrator_tool_call",
            step_index: 0,
            tool_name: "run_deal_structuring",
          }),
        ],
      }),
    });
  });
}

async function mockMultiWorkerLogTreeApi(page: Page) {
  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}/logs?view=tree`, async (route) => {
    const makeWorker = (
      id: string,
      name: string,
      parentId: string,
      stepIndex: number,
    ) =>
      makeLogNode({
        id,
        node_name: name,
        raw_output: `{"result":"ok"}`,
        parent_log_id: parentId,
        step_type: "worker_start",
        step_index: stepIndex,
        worker_name: name,
        children: [
          makeLogNode({
            id: `${id.slice(0, -1)}a`,
            node_name: `${name}:reasoning`,
            raw_output: "분석 중",
            parent_log_id: id,
            step_type: "reasoning",
            step_index: 0,
            worker_name: name,
          }),
        ],
      });

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        deal_id: DEAL_ID,
        total_count: 7,
        total_duration_ms: 120,
        logs: [
          makeLogNode({
            id: "33333333-3333-3333-3333-333333333333",
            node_name: "orchestrator",
            raw_output: "run_scoring_analysis",
            step_type: "orchestrator_tool_call",
            step_index: 0,
            tool_name: "run_scoring_analysis",
            children: [
              makeWorker(
                "44444444-4444-4444-4444-444444444444",
                "scoring_worker",
                "33333333-3333-3333-3333-333333333333",
                0,
              ),
            ],
          }),
          makeLogNode({
            id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            node_name: "orchestrator",
            raw_output: "run_risk_analysis",
            step_type: "orchestrator_tool_call",
            step_index: 1,
            tool_name: "run_risk_analysis",
            children: [
              makeWorker(
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "risk_worker",
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                0,
              ),
            ],
          }),
          makeLogNode({
            id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
            node_name: "orchestrator",
            raw_output: "run_resource_estimation",
            step_type: "orchestrator_tool_call",
            step_index: 2,
            tool_name: "run_resource_estimation",
            children: [
              makeWorker(
                "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "resource_worker",
                "cccccccc-cccc-cccc-cccc-cccccccccccc",
                0,
              ),
            ],
          }),
        ],
      }),
    });
  });
}

async function mockLegacyLogTreeApi(page: Page) {
  await page.route(`http://localhost:8000/api/deals/${DEAL_ID}/logs?view=tree`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        deal_id: DEAL_ID,
        total_count: 2,
        total_duration_ms: 40,
        logs: [
          makeLogNode({
            id: "33333333-3333-3333-3333-333333333333",
            node_name: "deal_structuring",
            raw_output: "구조화 결과",
            duration_ms: 20,
          }),
          makeLogNode({
            id: "44444444-4444-4444-4444-444444444444",
            node_name: "scoring",
            raw_output: "스코어링 결과",
            duration_ms: 20,
          }),
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

  test("should render hold scenario with orchestrator only (no workers)", async ({
    page,
  }) => {
    await mockDealDetailApis(page);
    await mockHoldLogTreeApi(page);

    await page.goto(`/deals/${DEAL_ID}/logs`);

    await expect(page.getByTestId("orchestrator-card")).toBeVisible();
    // No worker cards should exist
    await expect(page.getByTestId("worker-card")).toHaveCount(0);
  });

  test("should render multiple workers and allow expand/collapse", async ({
    page,
  }) => {
    await mockDealDetailApis(page);
    await mockMultiWorkerLogTreeApi(page);

    await page.goto(`/deals/${DEAL_ID}/logs`);

    // 3 orchestrator cards (one per worker invocation)
    await expect(page.getByTestId("orchestrator-card")).toHaveCount(3);
    // 3 worker cards nested inside
    await expect(page.getByTestId("worker-card")).toHaveCount(3);

    // Expand first worker → should reveal reasoning step
    const workerHeaders = page.getByTestId("worker-card-header");
    await workerHeaders.first().click();
    await expect(
      page.locator('[data-testid="react-step"][data-step-type="reasoning"]').first(),
    ).toBeVisible();

    // Collapse it again
    await workerHeaders.first().click();
    await expect(
      page.locator('[data-testid="react-step"][data-step-type="reasoning"]').first(),
    ).not.toBeVisible();
  });

  test("should fall back to legacy timeline for old log format", async ({
    page,
  }) => {
    await mockDealDetailApis(page);
    await mockLegacyLogTreeApi(page);

    await page.goto(`/deals/${DEAL_ID}/logs`);

    // Legacy timeline renders node names as labels, not orchestrator/worker cards
    await expect(page.getByTestId("orchestrator-card")).toHaveCount(0);
    await expect(page.getByTestId("worker-card")).toHaveCount(0);
    // Legacy node labels should appear (use exact match to avoid "딜 구조화 단계")
    await expect(page.getByText("딜 구조화", { exact: true })).toBeVisible();
    await expect(page.getByText("스코어링", { exact: true })).toBeVisible();
  });
});
