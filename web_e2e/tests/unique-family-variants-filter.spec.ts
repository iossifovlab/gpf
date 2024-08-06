import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Unique family variants filter tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });

  test('should disable unique family variants filter on a study', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compDenovo, 'Genotype Browser');
    await expect(page.locator('#unique-family-variants-block')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compDenovo, 'Gene Browser');
    await page.locator('gpf-gene-browser input#search-box').fill('SAMD11');
    await page.getByText('Go').click();
    await expect(page.locator('gpf-gene-plot')).toBeVisible();
    await expect(page.locator('#unique-family-variants-checkbox')).toBeDisabled();
  });

  test('should disable unique family variants when no variants are loaded', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.multi, 'Gene Browser');
    await page.locator('gpf-gene-browser input#search-box').fill('CHD8');
    await page.getByText('Go').click();
    await expect(page.locator('gpf-gene-plot')).toBeVisible();
    await expect(page.locator('#unique-family-variants-checkbox')).toBeDisabled();
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

  test('should use the unique family variants filter to hide variants', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype Browser');
    await expect(page.locator('#unique-family-variants-block')).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Gene Browser');
    await page.locator('gpf-gene-browser input#search-box').fill('SAMD11');
    await page.getByText('Go').click();
    await expect(page.locator('gpf-gene-plot')).toBeVisible();

    await expect(page.locator('#variants-count-span')).toHaveText('60 variants selected');
    await page.locator('#unique-family-variants-checkbox').click();
    await expect(page.locator('#variants-count-span')).toHaveText('30 variants selected');
  });
});
