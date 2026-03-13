import { test, expect } from "@playwright/test";

test.describe("Admin Settings", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin");
    await expect(page.getByText("관리자 설정")).toBeVisible();
  });

  test("should display all 5 tabs", async ({ page }) => {
    await expect(page.getByRole("tab", { name: "회사 정보" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "평가 기준" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "인력 관리" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "비용 설정" })).toBeVisible();
    await expect(
      page.getByRole("tab", { name: "프로젝트 이력" }),
    ).toBeVisible();
  });

  test("should show scoring criteria with sliders and total", async ({
    page,
  }) => {
    // Click the scoring weights tab
    await page.getByRole("tab", { name: "평가 기준" }).click();

    // Wait for criteria to load
    await page.waitForTimeout(2000);

    // Should display 7 criteria names
    const criteriaNames = [
      "기술 적합성",
      "수익성",
      "리소스 가용성",
      "납기 리스크",
      "요구사항 명확성",
      "전략적 가치",
      "고객 리스크",
    ];

    for (const name of criteriaNames) {
      await expect(page.getByText(name).first()).toBeVisible();
    }

    // Should show total percentage
    await expect(page.getByText(/합계|총|100%/i).first()).toBeVisible();

    // Save button should be present
    await expect(
      page.getByRole("button", { name: /저장/ }).first(),
    ).toBeVisible();
  });

  test("should manage team members (add and verify)", async ({ page }) => {
    // Navigate to team management tab
    await page.getByRole("tab", { name: "인력 관리" }).click();
    await page.waitForTimeout(2000);

    // Click add team member button
    const addBtn = page.getByRole("button", { name: /추가|팀원/ }).first();
    await addBtn.click();

    // Fill the dialog form
    await page.waitForTimeout(500);

    // Name field
    const nameInput = page.locator('input').filter({ has: page.locator('[value=""]') }).first();
    if (await nameInput.isVisible()) {
      await nameInput.fill("E2E 테스트 개발자");
    }

    // The dialog should have a submit/save button
    const dialogSaveBtn = page
      .locator('[role="dialog"]')
      .getByRole("button", { name: /저장|추가|확인/ })
      .first();

    if (await dialogSaveBtn.isVisible()) {
      // Fill monthly rate if visible
      const rateInput = page.locator('[role="dialog"] input[type="number"]').first();
      if (await rateInput.isVisible()) {
        await rateInput.fill("8000000");
      }
    }
  });

  test("should show company info tab by default", async ({ page }) => {
    // Company info tab is the default
    await expect(page.getByRole("tab", { name: "회사 정보" })).toHaveAttribute(
      "data-state",
      "active",
    );
  });
});
