import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Pheno tool measure tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');
  });

  test('should check if the dropdown menu closes when clicking outside', async({ page }) => {
    await page.locator('#search-box').click();
    await expect(page.locator('.measures-dropdown')).toBeVisible();

    await page.mouse.click(0, 0);
    await expect(page.locator('.measures-dropdown')).not.toBeVisible();
  });

  test('should check whether when the measure is empty, an error message appears' +
  'and the normalization checkboxes get disabled', async({ page }) => {
    await expect(page.getByText('Please select a measure.')).toBeVisible();
    await expect(page.getByLabel('Age')).toBeDisabled();
    await expect(page.getByLabel('Non verbal IQ')).toBeDisabled();

    await page.locator('#search-box').click();
    await page.getByText('instrument_1.measure_1').click();
    await expect(page.getByText('Please select a measure.')).not.toBeVisible();
    await expect(page.getByLabel('Age')).not.toBeDisabled();
    await expect(page.getByLabel('Non verbal IQ')).not.toBeDisabled();

    await page.locator('#clear-measure-button').click();
    await expect(page.getByText('Please select a measure.')).toBeVisible();
    await expect(page.getByLabel('Age')).toBeDisabled();
    await expect(page.getByLabel('Non verbal IQ')).toBeDisabled();
  });

  test('should check if the normalization checkboxes get disabled when' +
  'the measure is the same as the normalization criteria', async({ page }) => {
    await page.locator('#search-box').click();
    await page.getByText('instrument_1.age').click();
    await expect(page.getByLabel('Age')).toBeDisabled();

    await page.locator('#clear-measure-button').click();
    await page.locator('#search-box').click();
    await page.getByText('instrument_1.iq').click();
    await expect(page.getByLabel('Non verbal IQ')).toBeDisabled();
  });

  test('should check the remove button with selected measure', async({ page }) => {
    await page.locator('#search-box').click();
    await page.getByText('instrument_1.age').click();

    await page.locator('#clear-measure-button').click();
    await expect(page.locator('#search-box')).toBeEmpty();
  });

  [
    {
      searchText: 'age',
      options: ['instrument_1.age']
    },
    {
      searchText: 'm',
      options: ['instrument_1.measure_1', 'instrument_1.measure_2', 'instrument_1.measure_3', 'instrument_1.measure_4']
    },
    {
      searchText: 'q',
      options: ['instrument_1.iq']
    },
  ].forEach(data => {
    test(`should type ${data.searchText} and check available measures`, async({ page }) => {
      await page.locator('#search-box').click();
      await page.locator('#search-box').fill(data.searchText);
      await Promise.all(data.options.map(async(measure) => {
        await expect(page.locator('.measures-dropdown').getByText(measure)).toBeVisible();
      }));
    });
  });
});