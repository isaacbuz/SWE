import { test } from '@playwright/test';
import percySnapshot from '@percy/playwright';

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before taking snapshots
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('/dashboard');
  });

  test('Dashboard page snapshot', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Dashboard - Main View');
  });

  test('Agents page snapshot', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Agents - List View');

    // Click on first agent to show details
    await page.locator('[data-testid="agent-card"]').first().click();
    await percySnapshot(page, 'Agents - Detail View');
  });

  test('Tasks page snapshot', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Tasks - List View');

    // Open create task modal
    await page.getByRole('button', { name: /create task/i }).click();
    await percySnapshot(page, 'Tasks - Create Modal');
  });

  test('Projects page snapshot', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Projects - List View');
  });

  test('Workflows page snapshot', async ({ page }) => {
    await page.goto('/workflows');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Workflows - Overview');
  });

  test('Settings page snapshot', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Settings - Main View');
  });

  test('Dark mode snapshot', async ({ page }) => {
    await page.goto('/dashboard');

    // Toggle dark mode
    await page.getByRole('button', { name: /theme/i }).click();
    await page.getByRole('menuitem', { name: /dark/i }).click();

    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Dashboard - Dark Mode');
  });

  test('Mobile view snapshot', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await percySnapshot(page, 'Dashboard - Mobile View');
  });
});
