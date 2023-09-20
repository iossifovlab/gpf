import { Page, expect } from '@playwright/test';

export const instanceUrl = process.env.GPF_STAGING_INSTANCE_URL ? process.env.GPF_STAGING_INSTANCE_URL : 'http://dory.seqpipe.org:8000/hg38';
export const username = process.env.GPF_STAGING_USERNAME ? process.env.GPF_STAGING_USERNAME : 'admin@iossifovlab.com';
export const password = process.env.GPF_STAGING_PASSWORD ? process.env.GPF_STAGING_PASSWORD : 'secret';

export async function login(page: Page, user = username, pass = password): Promise<void> {
  await page.locator('#log-in-button').click();
  expect(page.url()).toContain('login');

  await page.locator('#id_username').fill(user);
  await page.locator('#id_password').fill(pass);
  await Promise.all([
    await page.waitForLoadState(),
    await page.locator('.login-button').click()
  ]);

  await page.waitForSelector('#log-out-button');
  await expect(page.getByText('Loading datasets...')).not.toBeVisible();
  await page.waitForLoadState('networkidle');
}
