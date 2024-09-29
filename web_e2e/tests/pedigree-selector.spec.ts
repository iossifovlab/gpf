import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';

test.describe('Pedigree selector tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.compAll, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    await expect(page.locator('gpf-pedigree-selector').getByText('Select at least one.')).not.toBeVisible();

    await page.locator('gpf-pedigree-selector').getByText('None').click();
    await expect(page.locator('gpf-pedigree-selector').getByText('Select at least one.')).toBeVisible();

    await page.locator('gpf-pedigree-selector').getByText('All').click();
    await expect(page.locator('gpf-pedigree-selector').getByText('Select at least one.')).not.toBeVisible();
  });

  test('should check/uncheck affected status checkboxes using "All" and "None" buttons', async({ page }) => {
    await page.locator('gpf-pedigree-selector').getByText('None').click();
    await Promise.all(['affected', 'unaffected'].map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));

    await page.locator('gpf-pedigree-selector').getByText('All').click();
    await Promise.all(['affected', 'unaffected'].map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).toBeChecked();
    }));
  });

  test('should check checkboxes of Affected status, Role and Phenotype', async({ page }) => {
    await expect(page.locator('gpf-pedigree-selector .checkbox')).toHaveCount(2);
    await expect(page.locator('gpf-pedigree-selector')).toContainText('affected');
    await expect(page.locator('gpf-pedigree-selector')).toContainText('unaffected');

    await page.locator('#pedigree-dropdown-menu-button').click();
    await page.getByText('Role').click();
    await expect(page.locator('gpf-pedigree-selector .checkbox')).toHaveCount(4);
    await expect(page.locator('gpf-pedigree-selector')).toContainText('mom');
    await expect(page.locator('gpf-pedigree-selector')).toContainText('dad');
    await expect(page.locator('gpf-pedigree-selector')).toContainText('proband');
    await expect(page.locator('gpf-pedigree-selector')).toContainText('sibling');

    await page.locator('#pedigree-dropdown-menu-button').click();
    await page.getByRole('link', { name: 'Phenotype', exact: true }).click();
    await expect(page.locator('gpf-pedigree-selector .checkbox')).toHaveCount(2);
    await expect(page.locator('gpf-pedigree-selector')).toContainText('autism');
    await expect(page.locator('gpf-pedigree-selector')).toContainText('unaffected');
  });
});