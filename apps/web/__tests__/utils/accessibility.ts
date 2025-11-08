import { configureAxe } from 'jest-axe';

// Configure axe for accessibility testing
export const axe = configureAxe({
  rules: {
    // Customize rules as needed
    'color-contrast': { enabled: true },
    'valid-aria-role': { enabled: true },
    'aria-required-children': { enabled: true },
    'aria-required-parent': { enabled: true },
    'button-name': { enabled: true },
    'image-alt': { enabled: true },
    'label': { enabled: true },
    'link-name': { enabled: true },
  },
});

// Helper to check for accessibility violations
export async function checkA11y(container: HTMLElement) {
  const results = await axe(container);

  if (results.violations.length > 0) {
    console.error('Accessibility violations:', results.violations);
  }

  return results;
}

// Common WCAG 2.2 AA checks
export const a11yChecks = {
  level: 'AA',
  version: '2.2',
};
