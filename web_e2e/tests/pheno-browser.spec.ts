import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as fs from 'fs';
import * as path from 'path';
import { scanCSV } from 'nodejs-polars';
import { PhenoBrowser } from './components/pheno-browser.component';

test.describe('Pheno browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype browser');
  });


  [
    {seachQuery: 'age'},
    {seachQuery: 'measure_5'}
  ].forEach(data => {
    test(`should filter the correct rows when typing "${data.seachQuery}" in the searchbox`, async({ page }) => {
      const phenoBrowser = new PhenoBrowser(page);
      await expect(phenoBrowser.instrumentCells).toHaveCount(9);

      await phenoBrowser.searchInput.fill(data.seachQuery);
      await expect(phenoBrowser.instrumentCells).toHaveCount(1);
    });
  });

  test('should filter the correct rows using the instruments dropdown', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    await phenoBrowser.instrumentDropdown.selectOption('instrument_1');
    await expect(phenoBrowser.instrumentCells).toHaveCount(7);

    await phenoBrowser.instrumentDropdown.selectOption('All instruments');
    await expect(phenoBrowser.instrumentCells).toHaveCount(9);
  });

  test('should show nothing found when searching with invalid values', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    await expect(phenoBrowser.instrumentCells).toHaveCount(9);

    await phenoBrowser.searchInput.fill('the age');
    await expect(phenoBrowser.instrumentCells).toHaveCount(0);
    await expect(phenoBrowser.nothingFound).toBeVisible();
    await expect(phenoBrowser.measuresCount(0)).toBeVisible();

    await phenoBrowser.searchInput.clear();

    await phenoBrowser.searchInput.fill('continuous');
    await expect(phenoBrowser.instrumentCells).toHaveCount(0);
    await expect(phenoBrowser.nothingFound).toBeVisible();
    await expect(phenoBrowser.measuresCount(0)).toBeVisible();
  });

  test('should check measure description', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    await expect(phenoBrowser.descriptionIcon('measure_1')).toBeVisible();
    await phenoBrowser.descriptionIcon('measure_1').click();

    await expect(phenoBrowser.tooltipInner).toBeVisible();
    await expect(phenoBrowser.tooltipInner)
      .toContainText('Measure 1, a normally distributed continuous measure with a mean of 80');

    await page.mouse.click(0, 0);
    await expect(phenoBrowser.tooltipInner).not.toBeVisible();
  });

  test('should have working table header sorting buttons', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    await phenoBrowser.columnHeader('Instrument').click();
    await expect(phenoBrowser.instrumentCells.nth(0)).toHaveText('instrument_2');

    await phenoBrowser.columnHeader('Pheno Measure').click();
    await expect(phenoBrowser.measureNameCells.nth(0)).toHaveText('measure_7 info');

    await phenoBrowser.columnHeader('Pheno Measure').click();
    await expect(phenoBrowser.measureNameCells.nth(0)).toHaveText('age info');

    await phenoBrowser.columnHeader('Pheno Measure').click();
    await expect(phenoBrowser.measureNameCells.nth(0)).toHaveText('measure_7 info');

    await phenoBrowser.columnHeader('male').first().click();
    await expect(phenoBrowser.regressionCell('age', 'Male').nth(0)).toHaveText('0.8406');
    await expect(phenoBrowser.regressionCell('age', 'Female').nth(0)).toHaveText('0.875');

    await phenoBrowser.columnHeader('male').first().click();
    await expect(phenoBrowser.regressionCell('age', 'Male').nth(0)).toHaveText('');
    await expect(phenoBrowser.regressionCell('age', 'Female').nth(0)).toHaveText('');
  });

  test('should have the correct text values in all rows', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    const expectedFile = fs.readFileSync(path.join(__dirname + '/../fixtures/pheno-browser/row_values.txt'), 'utf-8');
    const rowValues = expectedFile.split(',\n');

    /* eslint-disable no-await-in-loop */
    for (let i = 0; i < 9; i++) {
      const instrument = await phenoBrowser.instrumentCells.nth(i).textContent();
      const measureName = await phenoBrowser.measureNameCells.nth(i).textContent();
      const measureType = await phenoBrowser.measureTypeCells.nth(i).textContent();
      const age = await phenoBrowser.ageCells.nth(i).textContent();
      const iq = await phenoBrowser.iqCells.nth(i).textContent();

      const row = instrument + measureName + measureType + age + iq;
      expect(row).toBe(rowValues[i]);
    }
    /* eslint-enable no-await-in-loop */
  });

  test('should download all instruments and validate whether they are equal to the reference data', async({ page }) => {
    const phenoBrowser = new PhenoBrowser(page);
    await phenoBrowser.root.waitFor();

    let downloadPromise = page.waitForEvent('download');
    downloadPromise = page.waitForEvent('download');

    await phenoBrowser.downloadMeasures.click();
    const download = await downloadPromise;

    const downloadData = scanCSV(await download.path(), {sep: ',', nullValues: '-'});
    const fixtureData = scanCSV(
      'fixtures/pheno-browser/measures_hello_world.csv',
      {
        sep: ',',
        nullValues: '-'
      }
    );
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should serve pheno distribution images via /static/images/', async({ page, request }) => {
    // build_pheno_browser produces figure-distribution PNGs for the
    // helloworld pheno; the SPA renders them as <img class="table-chart">
    // with src='/static/images/pheno_helloworld/...'. This test catches
    // breakage in the apache /static/images/ alias (PHENO_IMAGES_DIR
    // env var) on either deployment shape — without it, all thumbnails
    // 404 silently and the page looks fine to a quick visual scan.
    const phenoBrowser = new PhenoBrowser(page);
    const thumbnail = phenoBrowser.tableChart.first();
    await thumbnail.scrollIntoViewIfNeeded();
    await expect(thumbnail).toBeVisible();

    // naturalWidth === 0 means the browser tried to load the image and
    // failed (404, decode error, ...). Real images are wider than 1px.
    const naturalWidth = await thumbnail.evaluate(
      (img) => (img as HTMLImageElement).naturalWidth
    );
    expect(naturalWidth).toBeGreaterThan(1);

    // Cross-check at the HTTP layer: the SPA might render the <img>
    // and silently fall back to a 0×0 if loaded, so probe the URL the
    // SPA actually emitted. The SPA composes src as a relative URL
    // ('static/images/...') and the browser resolves it via index.html's
    // <base href="/">; here we resolve it explicitly against frontendUrl.
    const src = await thumbnail.getAttribute('src');
    expect(src).toMatch(/static\/images\//);
    const absoluteSrc = new URL(src!, `${utils.frontendUrl}/`).toString();
    const response = await request.get(absoluteSrc);
    expect(response.ok()).toBe(true);
    expect(response.headers()['content-type']).toMatch(/^image\//);
  });
});
