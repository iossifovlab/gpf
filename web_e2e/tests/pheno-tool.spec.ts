import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Pheno tool tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype tool');
  });

  test('should display genes block panel', async({ page }) => {
    await expect(page.locator('gpf-genes-block')).toBeVisible();
  });

  test('should display pheno tool measure block panel', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-measure')).toBeVisible();
  });

  test('should display pheno tool genotype block panel', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-genotype-block')).toBeVisible();
  });

  test('should display family filters block panel', async({ page }) => {
    await expect(page.locator('gpf-family-filters-block')).toBeVisible();
  });

  test('should display "Report" button', async({ page }) => {
    await expect(page.getByText('Report')).toBeVisible();
  });

  test('should display "Share/save query" button', async({ page }) => {
    await expect(page.locator('#save-query-dropdown-button')).toBeVisible();
  });

  test('should display "Download" button', async({ page }) => {
    await expect(page.getByText('Download')).toBeVisible();
  });

  test('should display pheno tool results chart after "Report" button click', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();
    await expect(page.locator('gpf-pheno-tool-measure gpf-errors-alert .alert-danger')).toBeVisible();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await page.locator('gpf-pheno-tool').getByText('Report').click();
    await page.waitForSelector('gpf-pheno-tool-results-chart');
    await expect(page.locator('gpf-pheno-tool-results-chart')).toBeVisible();
  });

  test('should hide pheno tool results chart on state change', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();

    await page.getByPlaceholder('Select or start typing to search').click();
    await page.getByText('i1.age').first().click();
    await page.locator('gpf-pheno-tool').getByText('Report').click();
    await page.waitForSelector('gpf-pheno-tool-results-chart');
    await expect(page.locator('gpf-pheno-tool-results-chart')).toBeVisible();

    await page.locator('gpf-pheno-tool-effect-types button').getByText('None').click();

    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();
  });
});