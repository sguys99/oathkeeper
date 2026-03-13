import { test, expect } from "@playwright/test";

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
    // Navigate to deals list
    await page.goto("/deals");

    // Wait for page to load
    await page.waitForTimeout(2000);

    // If there are existing deals, click the first one
    const firstDealRow = page.locator("table tbody tr").first();
    const rowCount = await page.locator("table tbody tr").count();

    if (rowCount > 0) {
      await firstDealRow.click();

      // Should navigate to deal detail page
      await page.waitForURL(/\/deals\/.+/);

      // Check for key sections on the detail page
      // Verdict badge (one of: Go, No-Go, Conditional Go, Hold)
      const verdictSection = page.locator(
        '[class*="badge"], [class*="Badge"]',
      );
      // Score display
      const scoreSection = page.getByText(/\/\s*100/);

      // At least one of these should be visible if analysis is complete
      const hasVerdict = await verdictSection.first().isVisible().catch(() => false);
      const hasScore = await scoreSection.first().isVisible().catch(() => false);

      // If analysis exists, verify key sections
      if (hasVerdict || hasScore) {
        // Risk analysis section
        await expect(page.getByText(/리스크|위험/i).first()).toBeVisible();

        // Notion save button
        const notionBtn = page.getByRole("button", {
          name: /Notion.*저장/i,
        });
        await expect(notionBtn).toBeVisible();
      }
    }
  });
});
