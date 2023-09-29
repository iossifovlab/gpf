import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('User management tests for reset password in Users', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
  });

  test('should reset password', async({ page }) => {
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
  });
});
