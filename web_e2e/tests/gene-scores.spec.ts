import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';
import { scanCSV } from 'nodejs-polars';

test.describe('Gene scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display gene scores panel and dropdown and check default value', async({ page }) => {
    await expect(page.locator('#gene-scores-panel')).not.toBeVisible();
    await page.locator('#gene-scores').click();
    await expect(page.locator('#gene-scores-panel')).toBeVisible();
    await expect(page.locator('gpf-gene-scores select')).toContainText(
      'SFARI gene score - Evidence strength supporting a gene\'s association with autism'
    );
  });

  test('should visibility of from/to inputs for two scores', async({ page }) => {
    await page.locator('#gene-scores').click();
    await expect(page.locator('input#from-input-field')).not.toBeVisible();
    await expect(page.locator('input#to-input-field')).not.toBeVisible();

    await page.locator('gpf-gene-scores select').selectOption('pLI - Probability of Loss-of-Function Intolerance');
    await expect(page.locator('input#from-input-field')).toBeVisible();
    await expect(page.locator('input#to-input-field')).toBeVisible();
  });

  test('should have working from/to step up/down buttons in RVIS rank', async({ page }) => {
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS rank - Gene rank after sorting by RVIS intolerance score');

    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');

    await page.locator('.histogram-from .step.up').click();
    await page.waitForRequest(utils.backendUrl + '/api/v3/gene_scores/partitions');
    await page.locator('.histogram-to .step.down').click();
    await page.waitForRequest(utils.backendUrl + '/api/v3/gene_scores/partitions');
    await expect(page.locator('input#from-input-field')).toHaveValue('111.927');
    await expect(page.locator('input#to-input-field')).toHaveValue('16529.073');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');
  });

  test('should have working from/to step up/down buttons in ExAC pLI', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select').selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await expect(page.locator('input#from-input-field')).toHaveValue('0');
    await expect(page.locator('input#to-input-field')).toHaveValue('1');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-to .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.008');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.992');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-to .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.016');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.984');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.008');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.992');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0');
    await expect(page.locator('input#to-input-field')).toHaveValue('1');
  });

  test('should filter variants when RVIS rank gene score is selected', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await page.click('#gene-scores');
    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS rank - Gene rank after sorting by RVIS intolerance score');

    await expect(page.locator('text#sumOfBarsLabel')).not.toContainText('~');

    await page.locator('gpf-effect-types').getByRole('button', { name: 'All' }).click();
    await page.getByRole('button', { name: 'Table Preview' }).click();

    await expect(page.locator('#variants-count-span')).toHaveText('55 variants selected');
  });

  test('should download RVIS score and compare the file to the reference data', async({ page }) => {
    await page.click('#gene-scores');

    await page.locator('gpf-gene-scores select').selectOption('RVIS score - Intolerance of a gene to genetic variants');
    const downloadPromise = page.waitForEvent('download');
    await page.click('gpf-gene-scores .download-link');
    const downloadedFile = await downloadPromise;

    const streamData = downloadedFile.createReadStream();
    const data = [];

    for await (const chunk of await streamData) {
      data.push(chunk);
    }

    const expectedVariantsPath = path.join(__dirname + '/../fixtures/gene-scores/scores.csv');
    const expectedFileLines = await utils.readFile(expectedVariantsPath);
    const downloadedData = Buffer.concat(data);
    expect(downloadedData.toString()).toEqual(expectedFileLines.toString());
  });

  test('should type invalid and valid range start and check error state', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS score - Intolerance of a gene to genetic variants');

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('-100');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('0');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).not.toBeVisible();
    await expect(page.locator('gpf-gene-scores').locator('gpf-errors-alert')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();
  });

  test('should reset invalid gene scores state when switching to All tab', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS score - Intolerance of a gene to genetic variants');

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('-500');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('gpf-genes-block').getByRole('tab', { name: 'All' }).click();
    await expect(page.getByText('Range start should be more than or equal to domain min.')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();
  });

  test('should reset invalid gene scores state when switching to other tool', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('-1');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('a').filter({ hasText: 'Gene Browser'}).click();
    await page.locator('a').filter({ hasText: 'Genotype Browser'}).click();

    await expect(page.getByText('Range start should be more than or equal to domain min.')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();
  });

  test('should type range start less than domain min of number histogram', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('-1');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('should type range end more than domain max of number histogram', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await page.locator('#to-input-field').clear();
    await page.locator('#to-input-field').pressSequentially('10');
    await expect(page.getByText('Range end should be less than or equal to domain max.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('should type range end less than range start of number histogram', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await page.locator('#to-input-field').clear();
    await page.locator('#to-input-field').pressSequentially('-1');
    await expect(page.getByText('Range start should be less than or equal to range end.')).toBeVisible();
    await expect(page.getByText('Range end should be more than or equal to range start.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('should type range start more than range end of number histogram', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('pLI - Probability of Loss-of-Function Intolerance');

    await page.locator('#from-input-field').clear();
    await page.locator('#from-input-field').pressSequentially('2');
    await expect(page.getByText('Range start should be less than or equal to range end.')).toBeVisible();
    await expect(page.getByText('Range end should be more than or equal to range start.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });
});
test.describe('Gene scores categorical histogram tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('gene-score - Evidence strength supporting a gene\'s association with autism');
  });

  test('should switch historgam selection modes', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await expect(page.locator('.mat-mdc-menu-content').getByRole('menuitem')).toHaveCount(3);
    await expect(page.getByRole('menuitem', {name: 'range selector'})).toBeVisible();
    await expect(page.getByRole('menuitem', {name: 'click selector'})).toBeVisible();
    await expect(page.getByRole('menuitem', {name: 'dropdown selector'})).toBeVisible();

    await expect(page.getByRole('menuitem', {name: 'range selector'}))
      .toHaveCSS('background-color', 'rgb(42, 99, 149)');
    await expect(page.locator('[gpf-histogram-range-selector-line]')).toHaveCount(2);

    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await expect(page.locator('[gpf-histogram-range-selector-line]')).toHaveCount(0);

    await page.getByRole('button', {name: 'Mode'}).click();
    await expect(page.getByRole('menuitem', {name: 'click selector'}))
      .toHaveCSS('background-color', 'rgb(42, 99, 149)');

    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();
    await page.getByRole('button', {name: 'Mode'}).click();
    await expect(page.getByRole('menuitem', {name: 'dropdown selector'}))
      .toHaveCSS('background-color', 'rgb(42, 99, 149)');

    await expect(page.locator('[gpf-categorical-histogram]')).not.toBeVisible();
  });

  test('should check switch selection mode button is not visible for other histograms', async({ page }) => {
    await expect(page.locator('gpf-categorical-histogram')).toBeVisible();
    await expect(page.getByRole('button', {name: 'Mode'})).toBeVisible();
    await expect(page.locator('input#from-input-field')).not.toBeVisible();
    await expect(page.locator('input#to-input-field')).not.toBeVisible();

    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS score - Intolerance of a gene to genetic variants');
    await expect(page.getByRole('button', {name: 'Mode'})).not.toBeVisible();
    await expect(page.locator('gpf-histogram')).toBeVisible();
  });

  test('should check historgam colors change in range selector mode', async({ page }) => {
    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await page.locator('[gpf-histogram-range-selector-line]').nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(1000, 400, {steps: 3});
    await page.mouse.up();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');


    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(100, 400, {steps: 3});
    await page.mouse.up();

    await page.locator('[gpf-histogram-range-selector-line]').nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(1200, 400, {steps: 3});
    await page.mouse.up();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check historgam colors change in click selector mode', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await expect(page.getByText('Please select at least one value.')).toBeVisible();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await page.locator('rect[id="1"]').click();
    await expect(page.getByText('Please select at least one value.')).not.toBeVisible();
    await page.locator('rect[id="2"]').click();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await page.locator('rect[id="1"]').click();
    await page.locator('rect[id="2"]').click();

    await expect(page.getByText('Please select at least one value.')).toBeVisible();
    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should check if range selection is reset when switching to click selection', async({ page }) => {
    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'range selector'}).click();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check if click selection is reset when switching to range selection', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await page.locator('rect[id="3"]').click();
    await page.locator('rect[id="2"]').click();

    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'range selector'}).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should check if range selection is reset when selecting other histogram', async({ page }) => {
    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS score - Intolerance of a gene to genetic variants');
    await page.locator('gpf-gene-scores select')
      .selectOption('gene-score - Evidence strength supporting a gene\'s association with autism');

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check if click selection is reset when selecting other histogram', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await page.locator('rect[id="1"]').click();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await page.locator('gpf-gene-scores select')
      .selectOption('RVIS score - Intolerance of a gene to genetic variants');
    await page.locator('gpf-gene-scores select')
      .selectOption('gene-score - Evidence strength supporting a gene\'s association with autism');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should set ranges and share query', async({ page }) => {
    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should set ranges and download', async({ page }) => {
    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('playwright/fixtures/gene-scores/variants1.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should set ranges and check table results', async({ page }) => {
    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('87 variants selected');
  });

  test('should click histogram bars and share query', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="2"]').click();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('rect[id="1"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(page.locator('rect[id="2"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="3"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should click histogram bars and download', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="3"]').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('playwright/fixtures/gene-scores/variants2.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should click histogram bars and check table results', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="3"]').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('4 variants selected');
  });

  test('should select values from dropdown and validate', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await expect(page.getByText('Please select at least one value.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();

    await page.locator('#search-box').click();
    await page.locator('mat-option').getByText('2 (706)').click();

    await expect(page.getByText('Please select at least one value.')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();

    await expect(page.locator('.value-wrapper')).toBeVisible();
    await expect(page.locator('.remove-value')).toBeVisible();
    await expect(page.locator('.value-wrapper')).toContainText('2 (706)');

    await page.locator('#search-box').click();
    await expect(page.locator('mat-option:has-text("2 (706)")')).toBeDisabled();
  });

  test('should remove selected value from list of values and validate', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('3');
    await expect(page.locator('mat-option').getByText('2 (706)')).not.toBeVisible();
    await page.locator('mat-option').getByText('3 (143)').click();

    await page.locator('#search-box').click();
    await page.locator('mat-option').getByText('1 (233)').click();

    await expect(page.locator('#values-list')).toContainText('3 (143)');
    await expect(page.locator('#values-list')).toContainText('1 (233)');
    await expect(page.locator('.remove-value')).toHaveCount(2);

    await page.locator('.remove-value').nth(0).click();
    await page.locator('.remove-value').nth(0).click();

    await page.locator('#search-box').click();
    await expect(page.locator('mat-option:has-text("1 (233)")')).toBeEnabled();
    await expect(page.locator('mat-option:has-text("3 (143)")')).toBeEnabled();

    await expect(page.getByText('Please select at least one value.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
  });

  test('errors state reset when validation fails and switch tool', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await expect(page.locator('gpf-categorical-histogram')).toBeVisible();
    await expect(page.getByText('Please select at least one value.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();

    await page.locator('a').filter({ hasText: 'Gene browser'}).click();

    await page.locator('a').filter({ hasText: 'Genotype browser'}).click();

    await expect(page.locator('gpf-categorical-histogram')).not.toBeVisible();
    await expect(page.getByText('Please select at least one value.')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
  });

  test('should check save/share query when using dropdown selector', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await page.locator('#search-box').click();
    await page.locator('mat-option').getByText('3 (143)').click();

    await page.getByRole('button', { name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('#search-box')).toBeEmpty();
    await expect(page.locator('.value-wrapper')).toHaveCount(1);
    await expect(page.locator('#values-list')).toContainText('3 (143)');
  });

  test('should check downloading when using dropdown selector', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await page.locator('#search-box').click();
    await page.locator('mat-option').getByText('3 (143)').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('playwright/fixtures/gene-scores/variants3.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check table preview when using dropdown selector', async({ page }) => {
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await page.locator('#search-box').click();
    await page.locator('mat-option').getByText('3 (143)').click();

    await page.getByRole('button', { name: 'Table Preview'}).click();

    await expect(page.locator('#variants-count-span')).toHaveText('4 variants selected');
  });
});