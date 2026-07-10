import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { VariantTypes } from './components/variant-types.component';

test.describe('Variant types tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    const variantTypes = new VariantTypes(page);
    await expect(variantTypes.selectAtLeastOneError).not.toBeVisible();

    await variantTypes.button('None').click();
    await expect(variantTypes.selectAtLeastOneError).toBeVisible();

    await variantTypes.button('All').click();
    await expect(variantTypes.selectAtLeastOneError).not.toBeVisible();
  });

  test('should check/uncheck variant types checkboxes using "All" and "None" buttons', async({ page }) => {
    const variantTypes = new VariantTypes(page);
    await variantTypes.button('None').click();
    await expect(variantTypes.label('sub')).not.toBeChecked();
    await expect(variantTypes.label('ins')).not.toBeChecked();
    await expect(variantTypes.label('del')).not.toBeChecked();

    await variantTypes.button('All').click();
    await expect(variantTypes.label('sub')).toBeChecked();
    await expect(variantTypes.label('ins')).toBeChecked();
    await expect(variantTypes.label('del')).toBeChecked();
  });
});
