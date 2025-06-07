import { test, expect } from '@playwright/test';

test('homepage shows login link', async ({ page }) => {
  await page.goto('http://localhost:5173');
  const login = page.getByRole('button', { name: /login/i });
  await expect(login).toBeVisible();
});
