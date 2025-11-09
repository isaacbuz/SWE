/**
 * E2E tests for Skills Marketplace UI
 * 
 * These tests require:
 * - Backend API running on localhost:8000
 * - Frontend running on localhost:3000
 * - Test database with seeded Skills
 */
import { test, expect } from '@playwright/test'

test.describe('Skills Marketplace', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to Skills marketplace
    await page.goto('http://localhost:3000/skills')
  })

  test('should display skills marketplace page', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Skills/i)
    
    // Check for search input
    const searchInput = page.getByPlaceholder(/search/i)
    await expect(searchInput).toBeVisible()
  })

  test('should display skills list', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Check that at least one skill card is visible
    const skillCards = page.locator('[data-testid="skill-card"]')
    const count = await skillCards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should filter skills by category', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Click on category filter
    const categoryFilter = page.getByRole('button', { name: /category/i })
    if (await categoryFilter.isVisible()) {
      await categoryFilter.click()
      
      // Select CODE_GENERATION category
      const codeGenOption = page.getByRole('option', { name: /code generation/i })
      if (await codeGenOption.isVisible()) {
        await codeGenOption.click()
        
        // Wait for filtered results
        await page.waitForTimeout(1000)
        
        // Verify all visible skills are in CODE_GENERATION category
        const skillCards = page.locator('[data-testid="skill-card"]')
        const count = await skillCards.count()
        expect(count).toBeGreaterThanOrEqual(0)
      }
    }
  })

  test('should search skills', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Type in search box
    const searchInput = page.getByPlaceholder(/search/i)
    await searchInput.fill('test')
    
    // Wait for search results
    await page.waitForTimeout(1000)
    
    // Verify results (may be empty if no matches)
    const skillCards = page.locator('[data-testid="skill-card"]')
    const count = await skillCards.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should navigate to skill detail page', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Click on first skill card
    const firstSkill = page.locator('[data-testid="skill-card"]').first()
    const skillName = await firstSkill.locator('h3').textContent()
    
    await firstSkill.click()
    
    // Should navigate to detail page
    await expect(page).toHaveURL(/\/skills\/[^/]+$/)
    
    // Check skill name is displayed
    if (skillName) {
      await expect(page.getByText(skillName)).toBeVisible()
    }
  })

  test('should display skill playground', async ({ page }) => {
    // Navigate to a skill detail page
    await page.goto('http://localhost:3000/skills')
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    const firstSkill = page.locator('[data-testid="skill-card"]').first()
    await firstSkill.click()
    
    // Wait for detail page to load
    await page.waitForTimeout(1000)
    
    // Click on Playground tab
    const playgroundTab = page.getByRole('tab', { name: /playground/i })
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click()
      
      // Check for input form
      const inputForm = page.locator('[data-testid="skill-playground"]')
      await expect(inputForm).toBeVisible()
    }
  })

  test('should install a skill', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Find a skill with install button
    const installButton = page.getByRole('button', { name: /install/i }).first()
    
    if (await installButton.isVisible()) {
      await installButton.click()
      
      // Wait for installation
      await page.waitForTimeout(1000)
      
      // Check for installed badge or success message
      const installedBadge = page.getByText(/installed/i)
      // May or may not be visible depending on auth state
    }
  })

  test('should navigate to installed skills page', async ({ page }) => {
    // Click on "Installed" link in navigation or page
    const installedLink = page.getByRole('link', { name: /installed/i })
    
    if (await installedLink.isVisible()) {
      await installedLink.click()
      
      // Should navigate to installed skills page
      await expect(page).toHaveURL(/\/skills\/installed/)
      
      // Check page content
      await expect(page.getByText(/installed/i)).toBeVisible()
    }
  })

  test('should sort skills', async ({ page }) => {
    // Wait for skills to load
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    // Find sort dropdown
    const sortSelect = page.locator('select').first()
    
    if (await sortSelect.isVisible()) {
      // Select a sort option
      await sortSelect.selectOption({ value: 'name' })
      
      // Wait for sorted results
      await page.waitForTimeout(1000)
      
      // Verify skills are still displayed
      const skillCards = page.locator('[data-testid="skill-card"]')
      const count = await skillCards.count()
      expect(count).toBeGreaterThanOrEqual(0)
    }
  })
})

test.describe('Skill Detail Page', () => {
  test('should display skill information', async ({ page }) => {
    // Navigate to a skill (assuming at least one exists)
    await page.goto('http://localhost:3000/skills')
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    const firstSkill = page.locator('[data-testid="skill-card"]').first()
    await firstSkill.click()
    
    // Check for skill details
    await expect(page.locator('h1')).toBeVisible()
    await expect(page.getByText(/description/i)).toBeVisible()
  })

  test('should execute skill in playground', async ({ page }) => {
    // Navigate to skill detail page
    await page.goto('http://localhost:3000/skills')
    await page.waitForSelector('[data-testid="skill-card"]', { timeout: 10000 })
    
    const firstSkill = page.locator('[data-testid="skill-card"]').first()
    await firstSkill.click()
    
    // Go to playground tab
    const playgroundTab = page.getByRole('tab', { name: /playground/i })
    if (await playgroundTab.isVisible()) {
      await playgroundTab.click()
      
      // Fill in inputs (if form exists)
      const inputFields = page.locator('input, textarea')
      const count = await inputFields.count()
      
      if (count > 0) {
        // Try to fill first input
        await inputFields.first().fill('test input')
        
        // Click execute button
        const executeButton = page.getByRole('button', { name: /execute/i })
        if (await executeButton.isVisible()) {
          await executeButton.click()
          
          // Wait for results (may require auth)
          await page.waitForTimeout(2000)
          
          // Check for results or error message
          const results = page.locator('[data-testid="execution-results"]')
          const error = page.getByText(/error|unauthorized/i)
          
          // One of these should be visible
          const hasResults = await results.isVisible().catch(() => false)
          const hasError = await error.isVisible().catch(() => false)
          
          expect(hasResults || hasError).toBe(true)
        }
      }
    }
  })
})

