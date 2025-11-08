import { test, expect } from '@playwright/test';

test.describe('Agent Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('/dashboard');
    await page.goto('/agents');
  });

  test('should display agent list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /agents/i })).toBeVisible();

    // Check for agent cards
    const agentCards = page.locator('[data-testid="agent-card"]');
    await expect(agentCards.first()).toBeVisible();
  });

  test('should show agent details on click', async ({ page }) => {
    await page.locator('[data-testid="agent-card"]').first().click();

    // Verify details panel
    await expect(page.getByRole('heading', { name: /agent details/i })).toBeVisible();
    await expect(page.getByText(/status/i)).toBeVisible();
    await expect(page.getByText(/capabilities/i)).toBeVisible();
  });

  test('should filter agents by status', async ({ page }) => {
    await page.getByLabel(/filter by status/i).selectOption('available');

    const agents = page.locator('[data-testid="agent-card"]');
    const count = await agents.count();

    for (let i = 0; i < count; i++) {
      await expect(agents.nth(i)).toContainText(/available/i);
    }
  });

  test('should search agents by name', async ({ page }) => {
    await page.getByPlaceholder(/search agents/i).fill('Developer');

    const agents = page.locator('[data-testid="agent-card"]');
    await expect(agents.first()).toContainText(/developer/i);
  });

  test('should display agent metrics', async ({ page }) => {
    await page.locator('[data-testid="agent-card"]').first().click();

    await expect(page.getByText(/tasks completed/i)).toBeVisible();
    await expect(page.getByText(/success rate/i)).toBeVisible();
    await expect(page.getByText(/average time/i)).toBeVisible();
  });

  test('should handle agent state changes', async ({ page }) => {
    await page.locator('[data-testid="agent-card"]').first().click();

    const initialStatus = await page.getByText(/status:/).textContent();

    // Trigger state change (this would be done via WebSocket in real app)
    await page.getByRole('button', { name: /pause/i }).click();

    const newStatus = await page.getByText(/status:/).textContent();
    expect(newStatus).not.toBe(initialStatus);
  });
});
