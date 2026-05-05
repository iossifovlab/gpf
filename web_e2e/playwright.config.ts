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
  timeout: 600000,
  expect: {
    timeout: 60000,
    toHaveScreenshot: {
      maxDiffPixels: 100
    },
  },
  globalTimeout: 3600000,
  testDir: './tests',
  outputDir: './reports/test-results',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 0 : 0,
  /* Opt out of parallel tests on CI. */
  // Cap CI workers to 4. The compose-jenkins backend-e2e runs
  // gunicorn --workers=1 (workaround for the gpf-web Dataset
  // race condition) and can only serve ~4 concurrent variant
  // queries before /api/v3/genotype_browser/query starts
  // queueing past the test's 60s waitForRequest deadline.
  // Default (= CPU count, ~16 on the Jenkins agents) overwhelms
  // it and triggers timeouts in gene-browser specs that pass
  // locally at workers=4. Local-dev (no CI env var) keeps
  // Playwright's default parallelism since dev backends usually
  // have more capacity.
  workers: process.env.CI ? 4 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: process.env.JENKINS ? [['junit', { outputFile: './reports/junit-report.xml' }]] : [['html']],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.JENKINS ? 'http://frontend' : 'http://127.0.0.1:8080/gpf',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: process.env.JENKINS ? 'on' : 'on-first-retry',
    video: process.env.JENKINS ? { mode: 'retain-on-failure', size: { width: 1920, height: 1080 } }: { mode: 'retain-on-failure', size: { width: 1920, height: 1080 } },
    actionTimeout: 60000
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
