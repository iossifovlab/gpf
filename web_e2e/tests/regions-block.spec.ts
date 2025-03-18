import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Regions block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAllLiftover, 'Genotype browser');
  });

  test('should display regions filter panel', async({ page }) => {
    await expect(page.locator('#regions-filter-panel')).not.toBeVisible();
    await page.locator('#regions-filter').click();
    await expect(page.locator('#regions-filter-panel')).toBeVisible();
  });


  test('should display error alert in regions panel when the textarea is empty', async({ page }) => {
    await page.locator('#regions-filter').click();
    await expect(page.getByText('Invalid region!')).toBeVisible();

    await page.locator('gpf-regions-filter textarea').fill('1:865582');
    await expect(page.getByText('Invalid region!')).not.toBeVisible();
  });
});