import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as fs from 'fs';
import * as path from 'path';
import pl from 'nodejs-polars';

test.describe('Pheno browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
  });


  [
    {seachQuery: 'the age'},
    {seachQuery: 'measure 1'}
  ].forEach(data => {
    test(`should filter the right rows when typing "${data.seachQuery}" in the searchbox`, async({ page }) => {
      await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

      await expect(page.locator('gpf-table .table-row')).toHaveCount(8);

      await page.locator('input.form-control').fill(data.seachQuery);
      await expect(page.locator('gpf-table .table-row')).toHaveCount(1);
    });
  });

  test('should filter the right rows when typing "1" in the sarchbox', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

    await expect(page.locator('gpf-table .table-row')).toHaveCount(8);

    await page.locator('input.form-control').fill('1');
    await expect(page.locator('gpf-table .table-row')).toHaveCount(7);
  });

  test('should filter the right rows using the instruments dropdown', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');

    await expect(page.locator('gpf-table .table-row')).toHaveCount(8);

    await page.locator('select.form-control').selectOption('i1');
    await expect(page.locator('gpf-table .table-row')).toHaveCount(7);

    await page.locator('select.form-control').selectOption('pheno_common');
    await expect(page.locator('gpf-table .table-row')).toHaveCount(1);

    await page.locator('select.form-control').selectOption('All instruments');
    await expect(page.locator('gpf-table .table-row')).toHaveCount(8);
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
      page.locator('gpf-pheno-browser-table > gpf-table .table-row')
        .locator('gpf-table-view-cell').nth(1)).toHaveText('age');

    await page.locator('gpf-table-view-header-cell').nth(1).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table .table-row')
        .locator('gpf-table-view-cell').nth(1)).toHaveText('sample_id');

    await page.locator('gpf-table-view-header-cell').nth(2).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table .table-row')
        .locator('gpf-table-view-cell').nth(2)).toHaveText('The IQ of the individual');

    await page.locator('gpf-table-view-header-cell').nth(2).click();
    await expect(
      page.locator('gpf-pheno-browser-table > gpf-table .table-row')
        .locator('gpf-table-view-cell').nth(2)).toHaveText('');
  });

  test('should have the correct text values in all rows', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');

    const rowValues = expectedFile.split(',\n');

    for (let i = 0; i < rowValues.length; i++) {
      const row = page.locator('gpf-pheno-browser-table > gpf-table .table-row').nth(i);
      const text = await row.textContent();
      expect(text).toBe(rowValues[i]);
    }
  });
  test('should download all instruments and validate whether they are equal to the reference data', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');
    await page.waitForSelector('gpf-pheno-browser-table');

    let downloadPromise = page.waitForEvent('download');
    downloadPromise = page.waitForEvent('download');

    await page.locator('#download-measures').click();
    const download = await downloadPromise;

    const columnsToCheck = [
      'person_id',
      'i1.age',
      'i1.iq',
      'i1.m1',
      'i1.m2',
      'i1.m3',
      'i1.m4',
      'i1.m5',
      'pheno_common.sample_id'
    ];

    const fixtureFrame = (
      await pl
        .scanCSV(
          'playwright/fixtures/pheno-browser/measures_comp_all.csv',
          {
            sep: ',',
            nullValues: '-'
          }
        )
        .select(columnsToCheck)
        .collect()
    ).sort('person_id');

    const downloadFrame = (
      await pl
        .scanCSV(
          await download.path(),
          {
            sep: ',',
            nullValues: '-'
          }
        )
        .select(columnsToCheck)
        .collect()
    ).sort('person_id');
    expect(fixtureFrame.frameEqual(downloadFrame));
  });
});