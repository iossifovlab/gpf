import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Gene browser basic display tests before query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    await expect(page.locator('gpf-gender').getByText('Select at least one.')).not.toBeVisible();
    await page.locator('gpf-gender').getByText('None').click();
    await expect(page.locator('gpf-gender').getByText('Select at least one.')).toBeVisible();

    await page.locator('gpf-gender').getByText('All').click();
    await expect(page.locator('gpf-gender').getByText('Select at least one.')).not.toBeVisible();
  });

  test('should check/uncheck child gender checkboxes using "All" and "None" buttons', async({ page }) => {
    await page.locator('gpf-gender').getByText('None').click();
    await expect(page.locator('gpf-gender').locator('.male')).not.toBeChecked();
    await expect(page.locator('gpf-gender').locator('.female')).not.toBeChecked();
    await expect(page.locator('gpf-gender').locator('.unspecified')).not.toBeChecked();

    await page.locator('gpf-gender').getByText('All').click();
    await expect(page.locator('gpf-gender').locator('.male')).toBeChecked();
    await expect(page.locator('gpf-gender').locator('.female')).toBeChecked();
    await expect(page.locator('gpf-gender').locator('.unspecified')).toBeChecked();
  });
});