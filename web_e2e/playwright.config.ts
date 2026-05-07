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
    timeout: 15000,
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
  /* tb-g1z: 8→16 paired with gunicorn --workers 16 in
   * web/Dockerfile.production to keep the browser:backend ratio at 1:1. */
  workers: process.env.CI ? 16 : undefined,
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
    video: process.env.JENKINS ? { mode: 'retain-on-failure', size: { width: 1920, height: 1080 } }: { mode: 'retain-on-failure', size: { width: 1920, height: 1080 } },
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
