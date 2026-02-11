import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
    await page.goto('/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/AICinePipe/);
});

test('loads project list', async ({ page }) => {
    await page.goto('/');

    // Check for the main heading
    await expect(page.getByRole('heading', { name: 'AICinePipe' })).toBeVisible();

    // Check if "Add Project" card exists
    await expect(page.getByText('Add Project')).toBeVisible();
});
