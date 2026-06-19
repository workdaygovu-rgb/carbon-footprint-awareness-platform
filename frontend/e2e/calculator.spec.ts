import { test, expect } from "@playwright/test";

/**
 * E2E test: the critical user flow from input to results to saved history.
 *
 * Runs against the full stack in offline mode (USE_GEMINI=false,
 * USE_FIRESTORE=false) so results are deterministic (rule-based engine +
 * in-memory store) and no GCP credentials are needed.
 */
test.describe("Carbon Footprint Calculator Flow", () => {
  test("calculate footprint, view results and insights, save to history", async ({
    page,
  }) => {
    await page.goto("/");

    // ── Step 1: verify the form is visible ──────────────────────────
    await expect(page.getByRole("heading", { name: /estimate your annual footprint/i })).toBeVisible();

    // ── Step 2: fill out the form with specific values ──────────────
    await page.getByLabel(/car distance per week/i).fill("200");
    await page.getByLabel(/car fuel type/i).selectOption("petrol");
    await page.getByLabel(/public transit per week/i).fill("50");
    await page.getByLabel(/short-haul flights per year/i).fill("2");
    await page.getByLabel(/long-haul flights per year/i).fill("1");

    await page.getByLabel(/electricity per month/i).fill("300");
    await page.getByLabel(/natural gas per month/i).fill("150");
    await page.getByLabel(/people in household/i).fill("2");

    await page.getByLabel(/^diet$/i).selectOption("heavy_meat");
    await page.getByLabel(/goods spending per month/i).fill("500");
    await page.getByLabel(/landfill waste per week/i).fill("10");

    // ── Step 3: click calculate ─────────────────────────────────────
    await page.getByRole("button", { name: /calculate my footprint/i }).click();

    // ── Step 4: verify results section appears with totals ──────────
    await expect(page.getByRole("heading", { name: /your estimated footprint/i })).toBeVisible({
      timeout: 10_000,
    });
    // The total should appear as a formatted number with "CO₂e" unit.
    await expect(page.getByText(/CO₂e/).first()).toBeVisible();
    // The sustainable target comparison should be shown.
    await expect(page.getByText(/sustainable target/i).first()).toBeVisible();

    // ── Step 5: verify insights panel appears ───────────────────────
    await expect(page.getByRole("heading", { name: /personalized insights/i })).toBeVisible();
    // Source badge should say "Smart rules" (Gemini is disabled).
    await expect(page.getByText(/smart rules/i)).toBeVisible();
    // At least one recommendation should be visible.
    await expect(page.getByText(/potential saving/i).first()).toBeVisible();

    // ── Step 6: save the entry to history ───────────────────────────
    const saveButton = page.getByRole("button", { name: /save this entry/i });
    await expect(saveButton).toBeVisible();
    await saveButton.click();

    // ── Step 7: verify history table updates ────────────────────────
    // Wait for the history section to show at least one entry.
    await expect(page.getByRole("heading", { name: /your history/i })).toBeVisible();
    // The table should now have a row (the saved entry).
    const historyTable = page.locator("table.history").last();
    await expect(historyTable.locator("tbody tr")).toHaveCount(1, {
      timeout: 5_000,
    });
  });

  test("shows error message when API is unreachable", async ({ page }) => {
    // Block all API requests to simulate network failure.
    await page.route("/api/**", (route) => route.abort());

    await page.goto("/");
    await page.getByRole("button", { name: /calculate my footprint/i }).click();

    // The error alert should appear.
    await expect(page.getByRole("alert")).toContainText(/something went wrong/i, {
      timeout: 5_000,
    });
  });
});
