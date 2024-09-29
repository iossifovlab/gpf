import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Variant types tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    await expect(page.getByText('Select at least one.')).not.toBeVisible();

    await page.locator('gpf-variant-types button').getByText('None').click();
    await expect(page.getByText('Select at least one.')).toBeVisible();

    await page.locator('gpf-variant-types button').getByText('All').click();
    await expect(page.getByText('Select at least one.')).not.toBeVisible();
  });

  test('should check/uncheck variant types checkboxes using "All" and "None" buttons', async({ page }) => {
    await page.locator('gpf-variant-types button').getByText('None').click();
    await expect(page.getByLabel('sub', { exact: true })).not.toBeChecked();
    await expect(page.getByLabel('ins', { exact: true })).not.toBeChecked();
    await expect(page.getByLabel('del', { exact: true })).not.toBeChecked();

    await page.locator('gpf-variant-types button').getByText('All').click();
    await expect(page.getByLabel('sub', { exact: true })).toBeChecked();
    await expect(page.getByLabel('ins', { exact: true })).toBeChecked();
    await expect(page.getByLabel('del', { exact: true })).toBeChecked();
  });
});