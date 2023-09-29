import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('User management tests for reset password in Users', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
  });

  test('should reset password', async({ page }) => {
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;
    const password = 'XC^ZF*TZXuUChFsv';

    await utils.createUser(page, email, username);

    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText(email).click();
    await page.locator('#preview-plain > a').click();
    await page.goto(await page.locator('#preview-plain > a').getAttribute('href'), {waitUntil: 'load'});

    await page.locator('#id_new_password1').fill(password);
    await page.locator('#id_new_password2').fill(password);
    await page.locator('.login-button').click();

    await page.waitForSelector('gpf-gene-browser');
    await expect(page.locator('#log-out-button')).toBeVisible();
    await page.locator('#log-out-button').click();
  });
});
