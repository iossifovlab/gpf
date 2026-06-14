import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  timeout: 180000,
  expect: {
    /* tb-iuv: rolled back from 15000 → 60000 (pre-tb-g1z value).
     * Bisect of gpf-web-e2e #25 (no Mode A fails) → #26 (all 7 Mode A
     * fails) pinned the regression to tb-g1z's 60s→15s expect.timeout
     * cut. The 7 affected assertions are toHaveText('N variants
     * selected') after submitting variant queries on iossifov_2014 /
     * multi_liftover with specific filter combos (CHD8, GO terms,
     * effect types) — under 16-way gunicorn contention these queries
     * take 15–60s wall, so the tighter budget guaranteed timeout.
     * Restoring to 60s is the conservative rollback; a real perf fix
     * for the slow query paths is tracked separately (filed alongside
     * this commit, see br notes on tb-iuv). */
    timeout: 60000,
    toHaveScreenshot: {
      maxDiffPixels: 100
    },
  },
  globalTimeout: 1800000,
  testDir: './tests',
  outputDir: './reports/test-results',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* One retry on CI: makes trace='on-first-retry' actually fire and
   * surfaces flaky-but-passing tests in the JUnit report (Playwright
   * marks them `flaky`). Local stays at 0 retries for fast fail signal. */
  retries: process.env.CI ? 1 : 0,
  /* tb-iuv-fix: CI default 16 → 4. Reverts tb-g1z's 8→16 bump.
   * The variant query API is StreamingHttpResponse (SSE) on a sync
   * gunicorn worker that holds the connection for the whole stream
   * duration. With CI=16 Playwright workers, all 16 sync gunicorn
   * workers can be tied up simultaneously holding open streams,
   * queueing every other request — which surfaced as the "Loading
   * variants..." Mode A timeouts in builds #26-#37. Reproduced and
   * fixed by local iter1 (workers=4: 1 fail = orthogonal Mode B) and
   * iter2 (workers=8: 1 fail = same Mode B). 4 chosen over 8 for
   * conservative headroom — leaves 12 free gunicorn workers for
   * non-streaming requests at peak load. Costs ~5 min wall time vs
   * tb-g1z's bench (workers=4 = 16.7 min, workers=16 = ~6.5 min);
   * acceptable trade for stability.
   * tb-nxl: read E2E_WORKER_COUNT (single source of truth shared with
   * import_data.sh's per-worker user pool — see web_e2e/tests/utils.ts
   * loginWorkerUser). Bigger local CPUs can override via the env var
   * to keep parallelIndex bounded by the provisioned pool.
   * #933: default 4 → 8. The 4:4 ratio that tb-iuv-fix restored existed
   * only because the backend ran *sync* gunicorn. #931 switched the
   * split-mode e2e backend to gthread (--workers 4 --threads 4 =
   * 16-way concurrency), so SSE variant streams no longer pin a whole
   * process — 8 browsers stay at half the backend's request capacity,
   * generous headroom against the Mode A pile-ups, and a deliberately
   * smaller jump than the 16 that regressed before. */
  workers: parseInt(
    process.env.E2E_WORKER_COUNT ?? '8',
    10,
  ),
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: process.env.JENKINS ? [['junit', { outputFile: './reports/junit-report.xml' }]] : [['html']],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.JENKINS ? 'http://frontend' : 'http://127.0.0.1:8080/gpf',

    /* trace='on' generated a full trace.zip per test (~5–15 MB × 458 tests
     * = multi-GB artefact bundle) for green and red alike. With retries=1
     * the on-first-retry mode captures a trace only for tests that failed
     * once, which is the only case anyone reads the trace for anyway. */
    trace: process.env.JENKINS ? 'on-first-retry' : 'on-first-retry',
    /* tb-84q: CI mode 'on-first-retry' instead of 'retain-on-failure'.
     * 'retain-on-failure' starts ffmpeg at the beginning of every test
     * and deletes the file on pass — that means 16 concurrent 1080p
     * ffmpeg processes recording continuously across all green tests,
     * which overloads the Jenkins agent (observed on eyoree as >16
     * /ms-playwright/.../ffmpeg-linux processes contributing to the
     * tb-eqh MinIO timing-flake). 'on-first-retry' only records the
     * retry attempt; with retries=1 every failure still has video
     * evidence, but green tests never start ffmpeg. Same reasoning
     * the trace setting above already applies. Local stays at
     * retain-on-failure (no 16-way contention; retries=0 locally so
     * on-first-retry would record nothing). */
    video: process.env.JENKINS
      ? { mode: 'on-first-retry', size: { width: 1920, height: 1080 } }
      : { mode: 'retain-on-failure', size: { width: 1920, height: 1080 } },
    actionTimeout: 20000
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      }
    },
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  /* Run your local dev server before starting the tests */
  // webServer: {
  //   command: 'npm run start',
  //   url: 'http://127.0.0.1:3000',
  //   reuseExistingServer: !process.env.CI,
  // },
});
