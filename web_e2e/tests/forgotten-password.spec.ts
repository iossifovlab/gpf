import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Forgotten password tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
  });

  test('should open forgotten password window', async({ page }) => {
    await page.getByRole('button', { name: 'Log In' }).click();
    await expect(page.getByRole('link', {name: 'forgotten password'})).toBeVisible();
    await page.getByText('forgotten password').click();

    await expect(page.locator('input#id_email')).toBeVisible();
    await expect(page.getByRole('button', {name: 'Reset password'})).toBeVisible();
  });
});