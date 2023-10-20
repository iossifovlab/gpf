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

  test('should proplery disable the "Report", "Save/share query" and "Download" buttons on errors', async({
    page
  }) => {
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('#clear-measure-button').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();
    await page.locator('gpf-present-in-parent button').filter({ hasText: 'None'}).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('gpf-present-in-parent button').filter({ hasText: 'All' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('gpf-pheno-tool-effect-types button').filter({ hasText: 'None' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();
    await page.locator('gpf-pheno-tool-effect-types button').filter({ hasText: 'All' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('#family-ids').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('gpf-family-ids textarea').fill('f1');
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.getByText('Advanced').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.getByLabel('Advanced').getByPlaceholder('Select or start typing to search').click();
    await page.getByRole('button', { name: 'i1.age' }).first().click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();
  });
});