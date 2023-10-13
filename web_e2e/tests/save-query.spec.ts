import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Save query common tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, utils.toolPageLinks.genotypeBrowser);
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', 'dropdown-menu');
    await page.locator('#save-query-dropdown-button').click();
  });

  test('should display link input', async({ page }) => {
    await expect(page.locator('#link-input')).toBeVisible();
  });

  test('should display copy link button', async({ page }) => {
    await expect(page.locator('#copy-link-button')).toBeVisible();
  });

  test('should display name input', async({ page }) => {
    await expect(page.locator('gpf-save-query #name')).toBeVisible();
  });

  test('should display description input', async({ page }) => {
    await expect(page.locator('gpf-save-query #description')).toBeVisible();
  });

  test('should display save button', async({ page }) => {
    await expect(page.locator('gpf-save-query #save-button')).toBeVisible();
  });
});

test.describe('Save query tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
  });

  test('should open save query dropdown menu after pressing "Share/save query" button', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, utils.toolPageLinks.genotypeBrowser);
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', /dropdown-menu/);

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', /dropdown-menu show/);
  });

  test('should open save query dropdown menu, click on the copy link button ' +
     'and check whether the "Copied!" tooltip appears', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, utils.toolPageLinks.genotypeBrowser);
    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#copy-link-button')).toBeVisible();

    await expect(page.locator('ngb-tooltip-window')).not.toBeVisible();
    await page.locator('#copy-link-button').click();
    await expect(page.locator('ngb-tooltip-window')).toBeVisible();
  });
});
