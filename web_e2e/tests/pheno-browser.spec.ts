import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as fs from 'fs';
import * as path from 'path';
import { scanCSV } from 'nodejs-polars';

test.describe('Pheno browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype browser');
  });


  [
    {seachQuery: 'the third'},
    {seachQuery: 'measure_5'}
  ].forEach(data => {
    test(`should filter the correct rows when typing "${data.seachQuery}" in the searchbox`, async({ page }) => {
      await expect(page.locator('.instrument-cell')).toHaveCount(6);

      await page.locator('input.form-control').fill(data.seachQuery);
      await expect(page.locator('.instrument-cell')).toHaveCount(1);
    });
  });

  test('should filter the correct rows using the instruments dropdown', async({ page }) => {
    await page.locator('select.form-control').selectOption('instrument_1');
    await expect(page.locator('.instrument-cell')).toHaveCount(4);

    await page.locator('select.form-control').selectOption('All instruments');
    await expect(page.locator('.instrument-cell')).toHaveCount(6);
  });

  test('should have working table header sorting buttons', async({ page }) => {
    await page.getByText('Instrument', { exact: true }).click();
    await expect(page.locator('.instrument-cell').nth(0)).toHaveText('instrument_2');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('measure_6');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('measure_1');

    await page.getByText('Proband Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('measure_6');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('.reg_1').nth(0)).toHaveText('3.72e-73.04e-7');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('.reg_1').nth(0)).toHaveText('NaNNaN');
  });

  test('should have the correct text values in all rows', async({ page }) => {
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');

    const rowValues = expectedFile.split(',\n');

    await Promise.all(rowValues.map(async(val, i) => {
      const instrument = await page.locator('.instrument-cell').nth(i).textContent();
      const measureName = await page.locator('.measure-name-cell').nth(i).textContent();
      const description = await page.locator('.description-cell').nth(i).textContent();
      const measureType = await page.locator('.measure-type-cell ').nth(i).textContent();
      const reg1 = await page.locator('.reg_1').nth(i).textContent();


      const row = instrument + measureName + description + measureType + reg1;
      expect(row).toBe(val.trim());
    }));
  });

  test('should download all instruments and validate whether they are equal to the reference data', async({ page }) => {
    await page.waitForSelector('gpf-pheno-browser-table');

    let downloadPromise = page.waitForEvent('download');
    downloadPromise = page.waitForEvent('download');

    await page.locator('#download-measures').click();
    const download = await downloadPromise;

    const downloadData = scanCSV(await download.path(), {sep: ',', nullValues: '-'});
    const fixtureData = scanCSV(
      'playwright/fixtures/pheno-browser/measures_hello_world.csv',
      {
        sep: ',',
        nullValues: '-'
      }
    );
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.frameEqual(downloadFrame));
  });
});