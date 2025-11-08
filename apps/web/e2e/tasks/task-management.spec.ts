import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('/dashboard');

    // Navigate to tasks
    await page.goto('/tasks');
  });

  test('should display task list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /tasks/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /create task/i })).toBeVisible();
  });

  test('should create a new task', async ({ page }) => {
    await page.getByRole('button', { name: /create task/i }).click();

    // Fill task form
    await page.getByLabel(/title/i).fill('Test Task');
    await page.getByLabel(/description/i).fill('This is a test task');
    await page.getByLabel(/priority/i).selectOption('high');

    await page.getByRole('button', { name: /submit/i }).click();

    // Verify task was created
    await expect(page.getByText('Test Task')).toBeVisible();
  });

  test('should filter tasks by status', async ({ page }) => {
    await page.getByLabel(/filter by status/i).selectOption('completed');

    // Verify only completed tasks are shown
    const tasks = page.getByRole('listitem');
    await expect(tasks.first()).toContainText(/completed/i);
  });

  test('should assign task to agent', async ({ page }) => {
    // Click on first task
    await page.getByRole('listitem').first().click();

    // Open assignment dialog
    await page.getByRole('button', { name: /assign/i }).click();

    // Select agent
    await page.getByLabel(/select agent/i).selectOption('agent-1');
    await page.getByRole('button', { name: /confirm/i }).click();

    // Verify assignment
    await expect(page.getByText(/assigned to/i)).toBeVisible();
  });

  test('should update task status', async ({ page }) => {
    await page.getByRole('listitem').first().click();

    await page.getByLabel(/status/i).selectOption('in_progress');
    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText(/status updated/i)).toBeVisible();
  });

  test('should be accessible', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: /create task/i })).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByLabel(/filter/i)).toBeFocused();
  });
});
