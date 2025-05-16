import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Regions block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display regions filter panel', async({ page }) => {
    await expect(page.locator('#regions-filter-panel')).not.toBeVisible();
    await page.locator('#regions-filter').click();
    await expect(page.locator('#regions-filter-panel')).toBeVisible();
  });


  test('should display error alert in regions panel when the textarea is empty', async({ page }) => {
    await page.locator('#regions-filter').click();
    await expect(page.getByText('Add at least one region filter.')).toBeVisible();

    await page.locator('gpf-regions-filter textarea').pressSequentially('14:21393485');
    await expect(page.getByText('Invalid region: 14:21393485')).toBeVisible();

    await page.locator('gpf-regions-filter textarea').clear();
    await page.locator('gpf-regions-filter textarea').pressSequentially('chr14:21393485');
    await expect(page.locator('gpf-regions-filter').locator('gpf-errors-alert')).not.toBeVisible();
  });
});