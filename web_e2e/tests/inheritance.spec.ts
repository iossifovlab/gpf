import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';

test.describe('Inheritance selector tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.compAllLiftover, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    await expect(page.locator('gpf-inheritancetypes').getByText('Select at least one.')).not.toBeVisible();

    await page.locator('gpf-inheritancetypes').getByText('None').click();
    await expect(page.locator('gpf-inheritancetypes').getByText('Select at least one.')).toBeVisible();

    await page.locator('gpf-inheritancetypes').getByText('All').click();
    await expect(page.locator('gpf-inheritancetypes').getByText('Select at least one.')).not.toBeVisible();
  });

  test('should check/uncheck affected status checkboxes using "All" and "None" buttons', async({ page }) => {
    await expect(page.locator('gpf-pedigree-selector .checkbox')).toHaveCount(2);

    await page.locator('gpf-inheritancetypes').getByText('None').click();
    await Promise.all(['mendelian', 'denovo'].map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));

    await page.locator('gpf-inheritancetypes').getByText('All').click();
    await Promise.all(['mendelian', 'denovo'].map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).toBeChecked();
    }));
  });
});