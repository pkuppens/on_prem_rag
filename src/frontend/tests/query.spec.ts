import { test, expect } from '@playwright/test';

// QuerySection uses /api/ask (hybrid retrieval)
const emptyAskResponse = {
  answer: "I couldn't find relevant information.",
  sources: [],
  confidence: 'low',
  chunks_retrieved: 0,
  average_similarity: 0,
};

test.describe('Query Functionality', () => {
  test('should show no results message when ask returns empty sources', async ({ page }) => {
    await page.route('**/api/ask', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(emptyAskResponse),
      });
    });

    await page.goto('http://localhost:5173/');

    await page.getByLabel(/ask a question/i).fill('test query');
    await page.click('button:has-text("Ask")');

    await expect(page.locator('text=No relevant chunks found')).toBeVisible();
  });

  test('should show loading state during ask', async ({ page }) => {
    await page.route('**/api/ask', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(emptyAskResponse),
      });
    });

    await page.goto('http://localhost:5173/');

    await page.getByLabel(/ask a question/i).fill('test query');
    await page.click('button:has-text("Ask")');

    await expect(page.locator('[role="progressbar"]')).toBeVisible();

    await expect(page.locator('text=No relevant chunks found')).toBeVisible();
  });

  test('should show error message when API call fails', async ({ page }) => {
    await page.route('**/api/ask', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    });

    await page.goto('http://localhost:5173/');

    await page.getByLabel(/ask a question/i).fill('test query');
    await page.click('button:has-text("Ask")');

    await expect(page.locator('text=Failed to search documents')).toBeVisible();
  });
});
