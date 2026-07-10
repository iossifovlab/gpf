import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { InheritanceTypes } from './components/inheritance-types.component';

test.describe('Inheritance selector tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    const inheritanceTypes = new InheritanceTypes(page);
    await expect(inheritanceTypes.selectAtLeastOneError).not.toBeVisible();

    await inheritanceTypes.button('None').click();
    await expect(inheritanceTypes.selectAtLeastOneError).toBeVisible();

    await inheritanceTypes.button('All').click();
    await expect(inheritanceTypes.selectAtLeastOneError).not.toBeVisible();
  });

  test('should check/uncheck affected status checkboxes using "All" and "None" buttons', async({ page }) => {
    const inheritanceTypes = new InheritanceTypes(page);
    await expect(inheritanceTypes.checkboxes).toHaveCount(2);

    await inheritanceTypes.button('None').click();
    await Promise.all(['mendelian', 'denovo'].map(async(type) => {
      await expect(inheritanceTypes.label(type)).not.toBeChecked();
    }));

    await inheritanceTypes.button('All').click();
    await Promise.all(['mendelian', 'denovo'].map(async(type) => {
      await expect(inheritanceTypes.label(type)).toBeChecked();
    }));
  });
});
