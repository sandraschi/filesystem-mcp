import { expect, test } from "@playwright/test";

const BE = "http://127.0.0.1:10742";
const FE = "http://127.0.0.1:10743";

test.describe("Fleet Audit", () => {
  test("Backend health returns 200", async ({ request }) => {
    const resp = await request.get(`${BE}/api/health`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.status).toBe("healthy");
  });

  test("Backend capabilities list tools", async ({ request }) => {
    const resp = await request.get(`${BE}/api/capabilities`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.capabilities.tools.length).toBeGreaterThan(20);
  });

  test("Frontend loads without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto(FE, { timeout: 15000 });
    await expect(page.locator("#root")).toBeAttached();
    await page.waitForTimeout(3000);
    expect(errors).toEqual([]);
  });

  test("Dashboard renders with KPIs", async ({ page }) => {
    await page.goto(FE, { timeout: 15000 });
    await expect(page.getByTestId("dashboard")).toBeAttached();
    await expect(page.getByTestId("backend-dot")).toBeAttached();
  });
});
