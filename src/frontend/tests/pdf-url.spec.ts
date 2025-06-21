import { test, expect } from '@playwright/test';
import { apiUrls } from '../src/config/api';

test.describe('PDF URL Construction', () => {
  test('should construct correct PDF URL for backend endpoint', async ({ page }) => {
    // Navigate to a page that uses PDF viewer
    await page.goto('http://localhost:5173/?test=pdf');

    // Check that the test PDF URL is correct
    const testPdfUrl = apiUrls.file('2303.18223v16.pdf');

    // Verify the URL is accessible
    const response = await page.request.get(testPdfUrl);
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('application/pdf');
  });

  test('should serve uploaded PDF files correctly', async ({ page }) => {
    // Mock the file upload response
    await page.route('**/api/documents/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Document uploaded and processed successfully' })
      });
    });

    // Navigate to the PDF test page
    await page.goto('http://localhost:5173/?test=pdf');

    // Upload a test PDF file
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('text=Drag and drop files here');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('tests/test_data/2303.18223v16.pdf');

    // Wait for upload to complete
    await page.waitForSelector('text=Upload completed successfully', { timeout: 10000 });

    // Check that the PDF URL is updated correctly
    const pdfUrl = await page.locator('a[href*="api/documents/files"]').getAttribute('href');
    expect(pdfUrl).toBe(apiUrls.file('2303.18223v16.pdf'));
  });
});
