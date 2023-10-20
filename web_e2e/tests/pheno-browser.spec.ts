import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Pheno browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
  });


  [
    {seachQuery: 'the age'}
  ].forEach(data => {
    test(`should filter the right rows when typing "${data.seachQuery}" in the sarchbox`, async({ page }) => {
      await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

      await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(8);

      await page.locator('input.form-control').fill(data.seachQuery);
      await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(1);
    });
  });

  test('should filter the right rows when typing "1" in the sarchbox', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(8);

    await page.locator('input.form-control').fill('1');
    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(7);
  });

  test('should filter the right rows using the instruments dropdown', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(8);

    await page.locator('select.form-control').selectOption('i1');
    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(7);

    await page.locator('select.form-control').selectOption('pheno_common');
    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(1);

    await page.locator('select.form-control').selectOption('All instruments');
    await expect(page.locator('gpf-table > div > div.ng-star-inserted')).toHaveCount(8);
  });

  test('should have working table header sorting buttons', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

    await expect(page.locator('gpf-table-view-cell').nth(0)).toHaveText('i1');

    await page.locator('gpf-table-view-header-cell').nth(0).click();
    await expect(page.locator('gpf-table-view-cell').nth(0)).toHaveText('pheno_common');

    await page.locator('gpf-table-view-header-cell').nth(0).click();
    await expect(page.locator('gpf-table-view-cell').nth(0)).toHaveText('i1');

    await page.locator('gpf-table-view-header-cell').nth(1).click();
    await expect(page.locator('gpf-table-view-cell').nth(1)).toHaveText('sample_id');

    await page.locator('gpf-table-view-header-cell').nth(1).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted')
        .locator('gpf-table-view-cell').nth(1)).toHaveText('age');

    await page.locator('gpf-table-view-header-cell').nth(1).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted')
        .locator('gpf-table-view-cell').nth(1)).toHaveText('sample_id');

    await page.locator('gpf-table-view-header-cell').nth(2).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted')
        .locator('gpf-table-view-cell').nth(2)).toHaveText('The IQ of the individual');

    await page.locator('gpf-table-view-header-cell').nth(2).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted')
        .locator('gpf-table-view-cell').nth(2)).toHaveText('');
  });
  test('should have the correct text values in all rows', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');

    const rowValues = expectedFile.split(',\n');

    for (let i = 0; i < rowValues.length; i++) {
      const row = page.locator('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted').nth(i);
      // eslint-disable-next-line no-await-in-loop
      const text = await row.textContent();
      expect(text).toBe(rowValues[i]);
    }
  });
  test('should download all instruments and validate whether they are equal to the reference data', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');
    await page.waitForSelector('gpf-pheno-browser-table');
    const downloadBody = page.waitForEvent('download');
    await page.getByText('Download measures').click();
    const downloadBuffer = await downloadBody;
    const streamData = downloadBuffer.createReadStream();
    const data = [];

    for await (const chunk of await streamData) {
      data.push(chunk);
    }

    const expectedFileBuffer = fs.readFileSync(
      path.join(__dirname, '/../fixtures/pheno-browser/measures_comp_all.csv')
    );

    const downloadedData = Buffer.concat(data);
    expect(downloadedData.toString()).toEqual(expectedFileBuffer.toString());
  });
});