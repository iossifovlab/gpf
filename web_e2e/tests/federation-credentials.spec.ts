import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Federation token tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await page.locator('a:text("User Profile")').click();
    await page.getByText('Federation tokens').click();
  });

  test('should check federation tokens tab elements', async({ page }) => {
    await expect(page.locator('gpf-federation-credentials')).toBeVisible();
    await expect(page.locator('#new-credential-name-box')).toBeVisible();
    await expect(page.locator('#create-credential-button')).toBeVisible();
    await expect(page.getByText('Name', {exact: true})).toBeVisible();
    await expect(page.getByText('Actions', {exact: true})).toBeVisible();
  });

  test('should create new credential', async({ page }) => {
    await page.waitForSelector('.grid-container');
    await page.locator('#new-credential-name-box').fill('TestCredentials');
    await page.locator('#create-credential-button').click();
    await expect(page.locator('.credential-modal')).toBeVisible();
    await expect(page.locator('.credential-modal')).toContainText('Credentials: shown only once, copy before closing.');
    await page.locator('#copy-credentials-button').click();
    await expect(page.locator('#credential-modal-content')).not.toBeEmpty();

    await page.mouse.click(0, 0); // close modal
    await expect(page.locator('.credential-modal')).not.toBeVisible();

    await expect(page.locator('div[id="TestCredentials-name-cell"]')).toBeVisible();
    await expect(page.locator('div[id="TestCredentials-actions-cell"]')).toBeVisible();

    await page.locator('#TestCredentials-delete-credential-button').click();
    await page.getByRole('button', {name: 'Delete'}).click();
    await page.waitForSelector('div[id="TestCredentials-name-cell"]', {state: 'detached'});
  });

  test('should not create credential with invalid name', async({ page }) => {
    await page.waitForSelector('.grid-container');
    await page.locator('#new-credential-name-box').fill('a');
    await page.locator('#create-credential-button').click();
    await expect(page.getByText('Credential names must be at least 3 symbols long.')).toBeVisible();
    await expect(page.locator('#new-credential-name-box')).toBeFocused();
    await expect(page.locator('div[id="a-name-cell"]')).not.toBeVisible();

    await page.locator('#new-credential-name-box').fill('b');
    await page.locator('#create-credential-button').click();
    await expect(page.getByText('Credential names must be at least 3 symbols long.')).toBeVisible();
    await expect(page.locator('#new-credential-name-box')).toBeFocused();
    await expect(page.locator('div[id="ab-name-cell"]')).not.toBeVisible();
  });

  test('should not create credential with existing name', async({ page }) => {
    await page.waitForSelector('.grid-container');
    await page.locator('#new-credential-name-box').fill('ExistingCredential');
    await page.locator('#create-credential-button').click();

    await page.waitForSelector('.credential-modal');
    await page.mouse.click(0, 0); // close modal
    await expect(page.locator('div[id="ExistingCredential-name-cell"]')).toBeVisible();

    await page.locator('#new-credential-name-box').fill('ExistingCredential');
    await page.locator('#create-credential-button').click();
    await expect(page.getByText('Credential with such name already exists!')).toBeVisible();
    await expect(page.locator('#new-credential-name-box')).toBeFocused();

    await page.locator('#ExistingCredential-delete-credential-button').click();
    await page.getByRole('button', {name: 'Delete'}).click();
    await expect(page.locator('div[id="ExistingCredential-name-cell"]')).not.toBeVisible();
  });

  test('should rename credential', async({ page }) => {
    await page.waitForSelector('.grid-container');
    await page.locator('#new-credential-name-box').fill('RenameCredential');
    await page.locator('#create-credential-button').click();

    await page.waitForSelector('.credential-modal');
    await page.mouse.click(0, 0); // close modal
    await expect(page.locator('div[id="RenameCredential-name-cell"]')).toBeVisible();

    await page.locator('div[id="RenameCredential-name-cell"]').locator('#edit-icon').click();
    await expect(page.locator('#RenameCredential-new-name-input')).toBeVisible();
    await expect(page.locator('#cancel-button')).toBeVisible();

    await page.locator('#RenameCredential-new-name-input').clear();
    await page.locator('#RenameCredential-new-name-input').fill('NewNameCredential');
    await page.keyboard.press('Enter');

    await expect(page.locator('div[id="RenameCredential-name-cell"]')).not.toBeVisible();
    await expect(page.locator('div[id="NewNameCredential-name-cell"]')).toBeVisible();

    await page.locator('#NewNameCredential-delete-credential-button').click();
    await page.getByRole('button', {name: 'Delete'}).click();
    await expect(page.locator('div[id="NewNameCredential-name-cell"]')).not.toBeVisible();
  });

  test('should cancel renaming credential', async({ page }) => {
    await page.waitForSelector('.grid-container');
    await page.locator('#new-credential-name-box').fill('Credential');
    await page.locator('#create-credential-button').click();

    await page.waitForSelector('.credential-modal');
    await page.mouse.click(0, 0); // close modal
    await expect(page.locator('div[id="Credential-name-cell"]')).toBeVisible();

    await page.locator('div[id="Credential-name-cell"]').locator('#edit-icon').click();
    await page.locator('#Credential-new-name-input').clear();
    await page.locator('#Credential-new-name-input').fill('Credentialllll');
    await page.locator('#cancel-button').click();

    await expect(page.locator('div[id="Credentialllll-name-cell"]')).not.toBeVisible();
    await expect(page.locator('div[id="Credential-name-cell"]')).toBeVisible();

    await page.locator('#Credential-delete-credential-button').click();
    await page.getByRole('button', {name: 'Delete'}).click();
    await expect(page.locator('div[id="Credential-name-cell"]')).not.toBeVisible();
  });
});