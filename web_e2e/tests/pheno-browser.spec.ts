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
    {seachQuery: 'the age'},
    {seachQuery: 'measure_5'}
  ].forEach(data => {
    test(`should filter the correct rows when typing "${data.seachQuery}" in the searchbox`, async({ page }) => {
      await expect(page.locator('.instrument-cell')).toHaveCount(9);

      await page.locator('input.form-control').fill(data.seachQuery);
      await expect(page.locator('.instrument-cell')).toHaveCount(1);
    });
  });

  test('should filter the correct rows using the instruments dropdown', async({ page }) => {
    await page.locator('select.form-control').selectOption('instrument_1');
    await expect(page.locator('.instrument-cell')).toHaveCount(7);

    await page.locator('select.form-control').selectOption('All instruments');
    await expect(page.locator('.instrument-cell')).toHaveCount(9);
  });

  test('should have working table header sorting buttons', async({ page }) => {
    await page.getByText('Instrument', { exact: true }).click();
    await expect(page.locator('.instrument-cell').nth(0)).toHaveText('instrument_2');

    await page.getByText('Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('measure_7');

    await page.getByText('Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('age');

    await page.getByText('Pheno Measure', { exact: true }).click();
    await expect(page.locator('.measure-name-cell').nth(0)).toHaveText('measure_7');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('[class="age.pvalueRegressionMale"]').nth(0)).toHaveText('0.8406');
    await expect(page.locator('[class="age.pvalueRegressionFemale"]').nth(0)).toHaveText('0.875');

    await page.getByText('male', { exact: true }).first().click();
    await expect(page.locator('[class="age.pvalueRegressionMale"]').nth(0)).toHaveText('NaN');
    await expect(page.locator('[class="age.pvalueRegressionFemale"]').nth(0)).toHaveText('NaN');
  });

  test('should have the correct text values in all rows', async({ page }) => {
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');
    const rowValues = expectedFile.split(',\n');

    const instrument1 = await page.locator('.instrument-cell').nth(0).textContent();
    const measureName1 = await page.locator('.measure-name-cell').nth(0).textContent();
    const description1 = await page.locator('.description-cell').nth(0).textContent();
    const measureType1 = await page.locator('.measure-type-cell ').nth(0).textContent();
    const age1 = await page.locator('.age').nth(0).textContent();
    const iq1 = await page.locator('.iq').nth(0).textContent();

    const row1 = instrument1 + measureName1 + description1 + measureType1 + age1 + iq1;
    expect(row1).toBe(rowValues[0]);

    const instrument2 = await page.locator('.instrument-cell').nth(1).textContent();
    const measureName2 = await page.locator('.measure-name-cell').nth(1).textContent();
    const description2 = await page.locator('.description-cell').nth(1).textContent();
    const measureType2 = await page.locator('.measure-type-cell ').nth(1).textContent();
    const age2 = await page.locator('.age').nth(1).textContent();
    const iq2 = await page.locator('.iq').nth(1).textContent();

    const row2 = instrument2 + measureName2 + description2 + measureType2 + age2 + iq2;
    expect(row2).toBe(rowValues[1]);

    const instrument3 = await page.locator('.instrument-cell').nth(2).textContent();
    const measureName3 = await page.locator('.measure-name-cell').nth(2).textContent();
    const description3 = await page.locator('.description-cell').nth(2).textContent();
    const measureType3 = await page.locator('.measure-type-cell ').nth(2).textContent();
    const age3 = await page.locator('.age').nth(2).textContent();
    const iq3 = await page.locator('.iq').nth(2).textContent();

    const row3 = instrument3 + measureName3 + description3 + measureType3 + age3 + iq3;
    expect(row3).toBe(rowValues[2]);

    const instrument4 = await page.locator('.instrument-cell').nth(3).textContent();
    const measureName4 = await page.locator('.measure-name-cell').nth(3).textContent();
    const description4 = await page.locator('.description-cell').nth(3).textContent();
    const measureType4 = await page.locator('.measure-type-cell ').nth(3).textContent();
    const age4 = await page.locator('.age').nth(3).textContent();
    const iq4 = await page.locator('.iq').nth(3).textContent();

    const row4 = instrument4 + measureName4 + description4 + measureType4 + age4 + iq4;
    expect(row4).toBe(rowValues[3]);

    const instrument5 = await page.locator('.instrument-cell').nth(4).textContent();
    const measureName5 = await page.locator('.measure-name-cell').nth(4).textContent();
    const description5 = await page.locator('.description-cell').nth(4).textContent();
    const measureType5 = await page.locator('.measure-type-cell ').nth(4).textContent();
    const age5 = await page.locator('.age').nth(4).textContent();
    const iq5 = await page.locator('.iq').nth(4).textContent();

    const row5 = instrument5 + measureName5 + description5 + measureType5 + age5 + iq5;
    expect(row5).toBe(rowValues[4]);

    const instrument6 = await page.locator('.instrument-cell').nth(5).textContent();
    const measureName6 = await page.locator('.measure-name-cell').nth(5).textContent();
    const description6 = await page.locator('.description-cell').nth(5).textContent();
    const measureType6 = await page.locator('.measure-type-cell ').nth(5).textContent();
    const age6 = await page.locator('.age').nth(5).textContent();
    const iq6 = await page.locator('.iq').nth(5).textContent();

    const row6 = instrument6 + measureName6 + description6 + measureType6 + age6 + iq6;
    expect(row6).toBe(rowValues[5]);

    const instrument7 = await page.locator('.instrument-cell').nth(6).textContent();
    const measureName7 = await page.locator('.measure-name-cell').nth(6).textContent();
    const description7 = await page.locator('.description-cell').nth(6).textContent();
    const measureType7 = await page.locator('.measure-type-cell ').nth(6).textContent();
    const age7 = await page.locator('.age').nth(6).textContent();
    const iq7 = await page.locator('.iq').nth(6).textContent();

    const row7 = instrument7 + measureName7 + description7 + measureType7 + age7 + iq7;
    expect(row7).toBe(rowValues[6]);

    const instrument8 = await page.locator('.instrument-cell').nth(7).textContent();
    const measureName8 = await page.locator('.measure-name-cell').nth(7).textContent();
    const description8 = await page.locator('.description-cell').nth(7).textContent();
    const measureType8 = await page.locator('.measure-type-cell ').nth(7).textContent();
    const age8 = await page.locator('.age').nth(7).textContent();
    const iq8 = await page.locator('.iq').nth(7).textContent();

    const row8 = instrument8 + measureName8 + description8 + measureType8 + age8 + iq8;
    expect(row8).toBe(rowValues[7]);

    const instrument9 = await page.locator('.instrument-cell').nth(8).textContent();
    const measureName9 = await page.locator('.measure-name-cell').nth(8).textContent();
    const description9 = await page.locator('.description-cell').nth(8).textContent();
    const measureType9 = await page.locator('.measure-type-cell ').nth(8).textContent();
    const age9 = await page.locator('.age').nth(8).textContent();
    const iq9 = await page.locator('.iq').nth(8).textContent();

    const row9 = instrument9 + measureName9 + description9 + measureType9 + age9 + iq9;
    expect(row9).toBe(rowValues[8]);
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
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});