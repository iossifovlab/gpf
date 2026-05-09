// Literal-admin login. Distinct from utils.loginWorkerUser(): this hits
// admin@iossifovlab.com directly — the row asserted on by user-management.spec
// (#admin-list-item, [id="admin@iossifovlab.com-..."] selectors) and used for
// the four /management write-through tests that exercise the admin group
// (Management nav, nav-bar admin tabs, two access-rights writes).
//
// Do not import this file from any spec other than user-management.spec.ts.
// Jenkinsfile.e2e enforces this with a CI grep step (see tb-nxl). All other
// specs must use utils.loginWorkerUser() — which logs in as e2e_worker_<N>
// (any_dataset:any_user, no admin group), so accidental /management writes
// hit 403 instead of stomping the shared admin row under workers=16.

import { type Page, expect } from '@playwright/test';

export const LITERAL_ADMIN_EMAIL =
  process.env.GPF_STAGING_USERNAME ?? 'admin@iossifovlab.com';
export const LITERAL_ADMIN_PASSWORD =
  process.env.GPF_STAGING_PASSWORD ?? 'secret';

export async function loginLiteralAdmin(page: Page): Promise<void> {
  await page.locator('#log-in-button').click();
  expect(page.url()).toContain('login');

  await page.locator('#id_username').fill(LITERAL_ADMIN_EMAIL);
  await page.locator('#id_password').fill(LITERAL_ADMIN_PASSWORD);
  await Promise.all([
    page.waitForLoadState(),
    page.locator('.login-button').click(),
  ]);

  await page.waitForSelector('#log-out-button');
}
