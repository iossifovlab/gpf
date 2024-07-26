import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Unique family variants filter tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });

  test('should make unique family variants filter on a single study disabled', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype Browser');
    await expect(page.locator('#unique-family-variants-block')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Gene Browser');
    await page.locator('gpf-gene-browser input#search-box').fill('SAMD11');
    await page.getByText('Go').click();
    await expect(page.locator('gpf-gene-plot')).toBeVisible();
    await expect(page.locator('#unique-family-variants-checkbox')).toBeDisabled();
  });

  test.skip('should make the unique family variants filter on a dataset with only a single study disabled', async ({ page }) => {
    // ...
  });

  test('should enable the unique family variants filter on a dataset with at least 2 studies inside', async({ 
    page
  }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compGenotypes, 'Genotype Browser');
    await expect(page.locator('#unique-family-variants-block')).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compGenotypes, 'Gene Browser');
    await page.locator('gpf-gene-browser input#search-box').fill('SAMD11');
    await page.getByText('Go').click();
    await expect(page.locator('gpf-gene-plot')).toBeVisible();
    await expect(page.locator('#unique-family-variants-checkbox')).toBeEnabled();
  });

  test.skip('should use the unique family variants filter to hide variants', async({ page }) => {
    // ...
  });
});
