import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { Gender } from './components/gender.component';

test.describe('Gene browser basic display tests before query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    const gender = new Gender(page);
    await expect(gender.selectAtLeastOneError).not.toBeVisible();
    await gender.noneButton.click();
    await expect(gender.selectAtLeastOneError).toBeVisible();

    await gender.allButton.click();
    await expect(gender.selectAtLeastOneError).not.toBeVisible();
  });

  test('should check/uncheck child gender checkboxes using "All" and "None" buttons', async({ page }) => {
    const gender = new Gender(page);
    await gender.noneButton.click();
    await expect(gender.checkbox('male')).not.toBeChecked();
    await expect(gender.checkbox('female')).not.toBeChecked();
    await expect(gender.checkbox('unspecified')).not.toBeChecked();

    await gender.allButton.click();
    await expect(gender.checkbox('male')).toBeChecked();
    await expect(gender.checkbox('female')).toBeChecked();
    await expect(gender.checkbox('unspecified')).toBeChecked();
  });
});
