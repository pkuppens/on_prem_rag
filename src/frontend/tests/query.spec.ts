import { test, expect } from '@playwright/test';
import { apiUrls } from '../src/config/api';

test.describe('Query Functionality', () => {
  test('should show no results message when query returns empty results', async ({ page }) => {
    // Mock the API response to return empty results
    await page.route('**/api/query', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          primary_result: '',
          all_results: []
        })
      });
    });

    // Navigate to the query page
    await page.goto('http://localhost:5173/?test=query');

    // Enter a query
    await page.fill('input[placeholder*="query"], input[placeholder*="Query"], label:has-text("query") + input, label:has-text("Query") + input', 'test query');

    // Click search button
    await page.click('button:has-text("Search")');

    // Wait for the no results message to appear
    await expect(page.locator('text=No documents found matching your query')).toBeVisible();
  });

  test('should show loading state during query', async ({ page }) => {
    // Mock the API response with a delay
    await page.route('**/api/query', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          primary_result: '',
          all_results: []
        })
      });
    });

    // Navigate to the query page
    await page.goto('http://localhost:5173/?test=query');

    // Enter a query
    await page.fill('input[placeholder*="query"], input[placeholder*="Query"], label:has-text("query") + input, label:has-text("Query") + input', 'test query');

    // Click search button
    await page.click('button:has-text("Search")');

    // Check that loading state is shown
    await expect(page.locator('[role="progressbar"]')).toBeVisible();

    // Wait for the no results message to appear after loading
    await expect(page.locator('text=No documents found matching your query')).toBeVisible();
  });

  test('should show error message when API call fails', async ({ page }) => {
    // Mock the API response to return an error
    await page.route('**/api/query', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error'
        })
      });
    });

    // Navigate to the query page
    await page.goto('http://localhost:5173/?test=query');

    // Enter a query
    await page.fill('input[placeholder*="query"], input[placeholder*="Query"], label:has-text("query") + input, label:has-text("Query") + input', 'test query');

    // Click search button
    await page.click('button:has-text("Search")');

    // Wait for the error message to appear
    await expect(page.locator('text=Failed to search documents')).toBeVisible();
  });
});
