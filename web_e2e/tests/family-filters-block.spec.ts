import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';

test.describe('Family filters block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.compAll, 'Genotype browser');
  });

  test('should display family ids panel', async({ page }) => {
    await expect(page.locator('#family-ids-panel')).not.toBeVisible();
    await page.locator('#family-ids').click();
    await expect(page.locator('#family-ids-panel')).toBeVisible();
  });

  test('should display error alert in family ids panel when the textarea is empty', async({ page }) => {
    await page.locator('#family-ids').click();
    await expect(page.getByText('Please insert at least one family id.')).toBeVisible();

    await page.locator('gpf-family-ids textarea').fill('f1');
    await expect(page.getByText('Please insert at least one family id.')).not.toBeVisible();
  });

  test('should display pheno filters panel after "Advanced" button click', async({ page }) => {
    await expect(page.locator('gpf-family-filters-block').getByText('Advanced')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Advanced').click();

    await expect(page.locator('gpf-family-filters-block').locator('gpf-multi-continuous-filter')).toBeVisible();
    await expect(page.getByText('Select at least one continuous filter.')).toBeVisible();

    await page.locator('gpf-family-filters-block').locator('#search-box').click();
    await page.locator('.dropdown-menu').getByText('i1.age').click();
    await expect(page.locator('gpf-histogram')).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Advanced')).not.toBeVisible();
  });
});