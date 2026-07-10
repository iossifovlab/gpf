import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { Login } from './components/login.component';

test.describe('Forgotten password tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
  });

  test('should open forgotten password window', async({ page }) => {
    const loginComponent = new Login(page);
    await loginComponent.logInButton.click();
    await expect(loginComponent.forgottenPasswordLink).toBeVisible();
    await loginComponent.forgottenPasswordLink.click();

    await expect(loginComponent.emailInput).toBeVisible();
    await expect(loginComponent.resetPasswordButton).toBeVisible();
  });
});