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

    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype browser');
  });


  [
    {seachQuery: 'the age'},
    {seachQuery: 'measure 1'}
  ].forEach(data => {
    test(`should filter the right rows when typing "${data.seachQuery}" in the searchbox`, async({ page }) => {
      await expect(page.locator('.instrument-cell')).toHaveCount(8);

      await page.locator('input.form-control').fill(data.seachQuery);
      await expect(page.locator('.instrument-cell')).toHaveCount(1);
    });
  });

  test('should filter the right rows when typing "1" in the sarchbox', async({ page }) => {
    await expect(page.locator('.instrument-cell')).toHaveCount(8);

    await page.locator('input.form-control').fill('1');
    await expect(page.locator('.instrument-cell')).toHaveCount(7);
  });

  test('should filter the right rows using the instruments dropdown', async({ page }) => {
    await expect(page.locator('.instrument-cell')).toHaveCount(8);

    await page.locator('select.form-control').selectOption('i1');
    await expect(page.locator('.instrument-cell')).toHaveCount(7);

    await page.locator('select.form-control').selectOption('pheno_common');
    await expect(page.locator('.instrument-cell')).toHaveCount(1);

    await page.locator('select.form-control').selectOption('All instruments');
    await expect(page.locator('.instrument-cell')).toHaveCount(8);
  });

  test('should have working table header sorting buttons', async({ page }) => {
    await page.getByText('Instrument', { exact: true }).click();
    await expect(page.locator('.instrument-cell').nth(0)).toHaveText('pheno_common');

    await page.getByText('Instrument', { exact: true }).click();
    await expect(page.locator('.instrument-cell').nth(0)).toHaveText('i1');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('sample_id');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('age');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('sample_id');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('.age').nth(0)).toHaveText('0.97110.2512');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('.age').nth(0)).toHaveText('NaNNaN');
  });

  test('should have the correct text values in all rows', async({ page }) => {
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');

    const rowValues = expectedFile.split(',\n');

    await Promise.all(rowValues.map(async(val, i) => {
      const instrument = await page.locator('.instrument-cell').nth(i).textContent();
      const measureName = await page.locator('.measure-name-cell').nth(i).textContent();
      const description = await page.locator('.description-cell').nth(i).textContent();
      const measureType = await page.locator('.measure-type-cell ').nth(i).textContent();
      const age = await page.locator('.age').nth(i).textContent();
      const iq = await page.locator('.iq').nth(i).textContent();

      const row = instrument + measureName + description + measureType + age + iq;
      expect(row).toBe(val.trim());
    }));
  });

  test('should download all instruments and validate whether they are equal to the reference data', async({ page }) => {
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