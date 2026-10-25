import { readFileSync } from 'node:fs';
import { basename, extname, join } from 'node:path';
import { test, expect, type Page } from '@playwright/test';

// UI smoke test and demo walkthrough (#213). Each test is one demo step, in demo order;
// the talking points live in .claude/skills/smoke/SKILL.md. Start via `just smoke`.

interface KnownIssue {
  issue: string;
  summary: string;
  consoleErrorPattern?: string;
}

const env = (name: string, fallback: string) => process.env[name] ?? fallback;
const API_URL = env('SMOKE_API_URL', 'http://localhost:8000');
const FRONTEND_URL = env('SMOKE_FRONTEND_URL', 'http://localhost:5173');
const STREAMLIT_URL = env('SMOKE_STREAMLIT_URL', 'http://localhost:8501');
const CHAINLIT_URL = env('SMOKE_CHAINLIT_URL', 'http://localhost:8002');
const OUT = env('SMOKE_OUT', '../../tmp/debug/smoke');
const SAMPLE_DOC = env('SMOKE_SAMPLE_DOC', '../../tests/fixtures/metformin_summary.txt');
const SAMPLE_QUESTION = env('SMOKE_SAMPLE_QUESTION', 'What is metformin indicated for, and when is it contraindicated?');
// Async uploads store the file with a timestamp suffix: metformin_summary_1792748702.txt
const SAMPLE_STEM = basename(SAMPLE_DOC, extname(SAMPLE_DOC));
// Last sentence of the sample document: only visible when the full document renders, not in a chunk preview.
const SAMPLE_TAIL = 'titrate gradually';
const LLM_TIMEOUT = 180_000;

const KNOWN_ISSUES: Record<string, KnownIssue> = JSON.parse(
  readFileSync(new URL('./known-issues.json', import.meta.url), 'utf-8'),
);

/** Mark the current step as an expected failure when it has an open issue. Passing then fails the run: remove the entry. */
const expectKnownIssue = (key: string) => {
  const known = KNOWN_ISSUES[key];
  if (known) {
    test.info().annotations.push({ type: 'known-issue', description: `${known.issue} ${known.summary}` });
    test.fail(true, `Known issue ${known.issue}: ${known.summary}`);
  }
};

const knownConsolePatterns = Object.values(KNOWN_ISSUES)
  .filter((k) => k.consoleErrorPattern)
  .map((k) => new RegExp(k.consoleErrorPattern as string));

/** Collect console and page errors; errors covered by a known issue or by ``expected`` are ignored. */
const watchErrors = (page: Page, expected: RegExp[] = []) => {
  const errors: string[] = [];
  const ignored = [...knownConsolePatterns, ...expected];
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    const line = `${msg.text()} @ ${msg.location().url}`;
    if (!ignored.some((re) => re.test(line))) errors.push(line);
  });
  page.on('pageerror', (err) => errors.push(err.message));
  return errors;
};

const shot = (page: Page, name: string) => page.screenshot({ path: join(OUT, `${name}.png`), fullPage: true });

test.describe('React UI: upload, ask, cite', () => {
  test.describe.configure({ mode: 'serial' });

  let page: Page;
  let errors: string[];

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    errors = watchErrors(page);
  });

  test.afterEach(() => {
    expect(errors, 'browser console errors').toEqual([]);
    errors.length = 0;
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('01 react home: backend online, parameters, theme', async () => {
    await page.goto(FRONTEND_URL);
    await expect(page.getByText('Backend Online')).toBeVisible();
    await expect(page.getByText(/^LLM: /)).toBeVisible();
    await shot(page, '01-react-home');

    const background = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    const light = await background();
    await page.getByRole('combobox', { name: 'Theme' }).click();
    await page.getByRole('option', { name: 'Dark' }).click();
    await expect.poll(background).not.toBe(light);
    await shot(page, '01-react-dark');
    await page.getByRole('combobox', { name: 'Theme' }).click();
    await page.getByRole('option', { name: 'Light' }).click();
    await expect.poll(background).toBe(light);
  });

  test('02 react upload: drop a document', async () => {
    await page.locator('input[type="file"]').setInputFiles(SAMPLE_DOC);
    // The progress row shows while uploading and disappears once indexed; an error keeps it visible.
    const progress = page.getByText(basename(SAMPLE_DOC)).first();
    await expect(progress).toBeVisible();
    await shot(page, '02-react-uploading');
    await expect(progress).toBeHidden({ timeout: LLM_TIMEOUT });
    // After a reload the rows come from the backend's real state: none may be left behind once indexing is done.
    await page.reload();
    await expect(page.getByRole('progressbar')).toHaveCount(0, { timeout: LLM_TIMEOUT });
  });

  test('03 react ask: answer with numbered sources', async () => {
    await page.getByLabel('Ask a question').fill(SAMPLE_QUESTION);
    await expect(page.getByRole('button', { name: 'Start voice input' })).toBeVisible();
    await page.getByRole('button', { name: 'Ask', exact: true }).click();
    await expect(page.getByText('Answer', { exact: true })).toBeVisible({ timeout: LLM_TIMEOUT });
    await expect(page.getByText(/Sources \(\d+\)/)).toBeVisible();
    await expect(page.getByText(new RegExp(`${SAMPLE_STEM}.* Score: `)).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'View source 1' })).toBeVisible();
    await shot(page, '03-react-answer');
  });

  test('04 react document viewer: open the cited document', async () => {
    expectKnownIssue('react-document-viewer');
    await page.getByRole('button', { name: 'View source 1' }).click();
    await expect(page.getByText(SAMPLE_TAIL)).toBeVisible();
    await expect(page.getByText(/Failed to load/)).toHaveCount(0);
    await shot(page, '04-react-viewer');
  });

  test('05 react chat link: opens the Chainlit chat', async () => {
    expectKnownIssue('react-chat-link');
    const href = await page.getByRole('link', { name: 'Chat' }).getAttribute('href');
    expect(href?.replace(/\/$/, '')).toBe(CHAINLIT_URL);
  });
});

test('06 streamlit chat: answer with expandable sources', async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto(STREAMLIT_URL);
  await expect(page.getByRole('heading', { name: 'On-prem RAG chat' })).toBeVisible();
  await expect(page.getByRole('slider', { name: /Similarity threshold/ })).toBeVisible();
  await expect(page.getByRole('slider', { name: /Top k chunks/ })).toBeVisible();

  await page.getByTestId('stChatInputTextArea').fill(SAMPLE_QUESTION);
  await page.getByTestId('stChatInputTextArea').press('Enter');
  const source = page.getByTestId('stExpander').filter({ hasText: SAMPLE_STEM }).first();
  await expect(source).toBeVisible({ timeout: LLM_TIMEOUT });
  await source.getByText(SAMPLE_STEM).click();
  await shot(page, '06-streamlit-answer');
  expect(errors, 'browser console errors').toEqual([]);
});

test('07 chainlit chat: demo login shows the role welcome', async ({ page }) => {
  // Before login, Chainlit probes GET /user and logs the 401 as an error: expected, not a defect.
  const errors = watchErrors(page, [/401 \(Unauthorized\) @ .*\/user$/, /^vm: Unauthorized/]);
  await page.goto(CHAINLIT_URL);
  await expect(page.getByText('Login to access the app')).toBeVisible();
  await shot(page, '07-chainlit-login');
  // Demo users live in frontend.chat.auth.oauth_integration.DEMO_USERS.
  await page.locator('#email').fill('gp');
  await page.locator('#password').fill('gp123');
  await page.getByRole('button', { name: 'Sign In' }).click();
  await expect(page.getByText('Welcome, Dr. Demo GP!')).toBeVisible({ timeout: 30_000 });
  await shot(page, '07-chainlit-welcome');
  expect(errors, 'browser console errors').toEqual([]);
});

test('08 api docs: OpenAPI explorer', async ({ page }) => {
  await page.goto(`${API_URL}/docs`);
  await expect(page.getByText('/api/v1/qa').first()).toBeVisible();
  await shot(page, '08-api-docs');
});
