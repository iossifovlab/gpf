import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { PedigreeSelector } from './components/pedigree-selector.component';

test.describe('Pedigree selector tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    const pedigreeSelector = new PedigreeSelector(page);
    await expect(pedigreeSelector.selectAtLeastOneError).not.toBeVisible();

    await pedigreeSelector.noneButton.click();
    await expect(pedigreeSelector.selectAtLeastOneError).toBeVisible();

    await pedigreeSelector.allButton.click();
    await expect(pedigreeSelector.selectAtLeastOneError).not.toBeVisible();
  });

  test('should check/uncheck affected status checkboxes using "All" and "None" buttons', async({ page }) => {
    const pedigreeSelector = new PedigreeSelector(page);
    await pedigreeSelector.noneButton.click();
    await Promise.all(['affected', 'unaffected'].map(async(type) => {
      await expect(pedigreeSelector.label(type)).not.toBeChecked();
    }));

    await pedigreeSelector.allButton.click();
    await Promise.all(['affected', 'unaffected'].map(async(type) => {
      await expect(pedigreeSelector.label(type)).toBeChecked();
    }));
  });

  test('should check checkboxes of Affected status, Role and Phenotype', async({ page }) => {
    const pedigreeSelector = new PedigreeSelector(page);
    await expect(pedigreeSelector.checkboxes).toHaveCount(2);
    await expect(pedigreeSelector.root).toContainText('affected');
    await expect(pedigreeSelector.root).toContainText('unaffected');

    await pedigreeSelector.openCategory('Role');
    await expect(pedigreeSelector.checkboxes).toHaveCount(4);
    await expect(pedigreeSelector.root).toContainText('mom');
    await expect(pedigreeSelector.root).toContainText('dad');
    await expect(pedigreeSelector.root).toContainText('proband');
    await expect(pedigreeSelector.root).toContainText('sibling');

    await pedigreeSelector.openCategory('Phenotype');
    await expect(pedigreeSelector.checkboxes).toHaveCount(2);
    await expect(pedigreeSelector.root).toContainText('autism');
    await expect(pedigreeSelector.root).toContainText('unaffected');
  });
});
