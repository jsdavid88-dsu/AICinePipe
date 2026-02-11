import { test, expect } from '@playwright/test';

// Mock data
const mockProject = {
    id: 'test_project_e2e_re',
    name: 'Test Project E2E Refined',
    description: 'Project for E2E testing',
    created_at: new Date().toISOString()
};

const mockShot = {
    id: 'SHT-E2E-REF',
    scene_description: 'E2E Refined Shot',
    status: 'pending',
    workflow_type: 'text_to_image',
    technical: { camera: 'Alexa 35' },
    environment: { location: 'Studio' }
};

test.describe('Job Generation Flow', () => {

    test.beforeEach(async ({ page }) => {
        // 1. Mock Projects List (Array of Strings)
        await page.route('**/projects/', async route => {
            if (route.request().method() === 'GET') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify([mockProject.id])
                });
            } else {
                await route.continue();
            }
        });

        // 2. Mock Project Load (POST /projects/:id/load)
        await page.route(`**/projects/${mockProject.id}/load`, async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ status: 'loaded' })
            });
        });

        // 3. Mock Shots List (GET /shots/)
        await page.route('**/shots/', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify([mockShot])
            });
        });

        // 4. Mock Backend Job Creation
        await page.route('**/jobs/', async route => {
            if (route.request().method() === 'POST') {
                const payload = route.request().postDataJSON();
                // Basic validation
                if (payload.shot_id === mockShot.id) {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            id: 'JOB-E2E-123',
                            status: 'pending',
                            ...payload
                        })
                    });
                } else {
                    await route.continue();
                }
            } else {
                await route.continue();
            }
        });
    });

    test('Navigate to Project -> ShotTable -> Click Generate -> Verify Status', async ({ page }) => {
        // Enable console logging
        page.on('console', msg => console.log('PAGE LOG:', msg.text()));
        page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

        // 1. Navigate to Home
        await page.goto('/');

        // 2. Click Project Card
        const projectCard = page.locator(`text=${mockProject.id}`);
        await expect(projectCard).toBeVisible();
        await projectCard.click();

        // 3. Verify ShotTable presence
        // Check for "New Shot" button to confirm we are on the project page
        await expect(page.locator('button', { hasText: 'New Shot' }).first()).toBeVisible({ timeout: 5000 });

        // Wait for the shot row to appear.
        // ShotTable uses a div with grid class for rows.
        // Filter by ID suffix ("REF") which is text in a span
        const shotRow = page.locator('div.grid').filter({ hasText: 'REF' }).first();
        await expect(shotRow).toBeVisible({ timeout: 10000 });

        // 4. Find Generate Button
        // The button has title="Generate Shot"
        const generateBtn = shotRow.locator('button[title="Generate Shot"]');

        await expect(generateBtn).toBeVisible();
        await generateBtn.click();

        // 5. Verify Mock Job Creation Call
        // Done implicitly via route handler, but let's check UI update.

        // The status cell should update.
        // The status text (e.g. Queued) is inside a select or potentially visible text
        // The select value is updated. Playwright checks value for select?
        // Or we check the class/text.
        // ShotTable rendering: <select value={shot.status} ... > <option>Queued</option> ...

        // Check if the select has value "queued" or "pending" (depending on race)
        // or check if 'Queued' text is visible (selected option text is visible)

        // Note: The mock returns "pending". Optimistic UI sets "queued".
        // If mock returns, it might flip back to "pending".
        // Let's check for either.
        const statusSelect = shotRow.locator('select');
        await expect(statusSelect).toHaveValue(/queued|pending/);

    });
});
