import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';
import { scanCSV } from 'nodejs-polars';
import { GenotypeBrowserPage } from './pages/genotype-browser.page';

test.describe('Gene scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display gene scores panel and dropdown and check default value', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneScoresPanel).not.toBeVisible();
    await genotypeBrowser.genes.openGeneScores();
    await expect(genotypeBrowser.genes.geneScoresPanel).toBeVisible();
    await expect(genotypeBrowser.genes.geneScores.select).toContainText(
      'SFARI gene score - Evidence strength supporting a gene\'s association with autism'
    );
  });

  test('should visibility of from/to inputs for two scores', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneScores = genotypeBrowser.genes.geneScores;
    await genotypeBrowser.genes.openGeneScores();
    await expect(geneScores.numberHistogram.fromInput).not.toBeVisible();
    await expect(geneScores.numberHistogram.toInput).not.toBeVisible();

    await geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');
    await expect(geneScores.numberHistogram.fromInput).toBeVisible();
    await expect(geneScores.numberHistogram.toInput).toBeVisible();
  });

  test('should have working from/to step up/down buttons in RVIS_rank', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('RVIS_rank - Gene rank after sorting by RVIS intolerance score');

    await expect(numberHistogram.fromInput).toHaveValue('1');
    await expect(numberHistogram.toInput).toHaveValue('16640');

    // Promise.all so waitForRequest registers BEFORE the click; otherwise
    // the 100ms partition-request debounce can fire before the click action
    // returns, and the post-click waitForRequest misses the request and
    // times out.
    await Promise.all([
      page.waitForRequest(utils.backendUrl + '/api/v3/gene_scores/partitions'),
      numberHistogram.stepFromUp.click(),
    ]);
    await Promise.all([
      page.waitForRequest(utils.backendUrl + '/api/v3/gene_scores/partitions'),
      numberHistogram.stepToDown.click(),
    ]);
    await expect(numberHistogram.fromInput).toHaveValue('111.927');
    await expect(numberHistogram.toInput).toHaveValue('16529.073');

    await numberHistogram.stepToUp.click();
    await numberHistogram.stepFromDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('1');
    await expect(numberHistogram.toInput).toHaveValue('16640');

    await numberHistogram.stepFromUp.click();
    await numberHistogram.stepFromDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('1');
    await expect(numberHistogram.toInput).toHaveValue('16640');
  });

  test('should have working from/to step up/down buttons in ExAC pLI', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await expect(numberHistogram.fromInput).toHaveValue('0');
    await expect(numberHistogram.toInput).toHaveValue('1');

    await numberHistogram.stepFromUp.click();
    await numberHistogram.stepToDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('0.008');
    await expect(numberHistogram.toInput).toHaveValue('0.992');

    await numberHistogram.stepFromUp.click();
    await numberHistogram.stepToDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('0.016');
    await expect(numberHistogram.toInput).toHaveValue('0.984');

    await numberHistogram.stepToUp.click();
    await numberHistogram.stepFromDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('0.008');
    await expect(numberHistogram.toInput).toHaveValue('0.992');

    await numberHistogram.stepToUp.click();
    await numberHistogram.stepFromDown.click();
    await expect(numberHistogram.fromInput).toHaveValue('0');
    await expect(numberHistogram.toInput).toHaveValue('1');
  });

  test('should filter variants when RVIS_rank gene score is selected', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('RVIS_rank - Gene rank after sorting by RVIS intolerance score');

    await expect(genotypeBrowser.genes.geneScores.numberHistogram.sumOfBarsLabel).not.toContainText('~');

    await page.locator('gpf-effect-types').getByRole('button', { name: 'All' }).click();
    await genotypeBrowser.runTablePreview();

    await expect(genotypeBrowser.variantsCount).toHaveText('55 variants selected');
  });

  test('should download RVIS score and compare the file to the reference data', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneScores();

    await genotypeBrowser.genes.geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');
    const downloadPromise = page.waitForEvent('download');
    await genotypeBrowser.genes.geneScores.downloadLink.click();
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
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('-100');
    await expect(numberHistogram.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('0');
    await expect(numberHistogram.rangeStartBelowMinError).not.toBeVisible();
    await expect(genotypeBrowser.genes.geneScores.errorsAlert).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should reset invalid gene scores state when switching to All tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('-500');
    await expect(numberHistogram.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.genes.openAllTab();
    await expect(numberHistogram.rangeStartBelowMinError).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should reset invalid gene scores state when switching to other tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('-1');
    await expect(numberHistogram.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.openToolLink('Gene Browser');
    await genotypeBrowser.openToolLink('Genotype Browser');

    await expect(numberHistogram.rangeStartBelowMinError).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should type range start less than domain min of number histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('-1');
    await expect(numberHistogram.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('should type range end more than domain max of number histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await numberHistogram.toInput.clear();
    await numberHistogram.toInput.pressSequentially('10');
    await expect(numberHistogram.rangeEndAboveMaxError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('should type range end less than range start of number histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await numberHistogram.toInput.clear();
    await numberHistogram.toInput.pressSequentially('-1');
    await expect(numberHistogram.rangeStartAfterEndError).toBeVisible();
    await expect(numberHistogram.rangeEndBeforeStartError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('should type range start more than range end of number histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const numberHistogram = genotypeBrowser.genes.geneScores.numberHistogram;
    await genotypeBrowser.genes.openGeneScoresTab();
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore('pLI - Probability of Loss-of-Function Intolerance');

    await numberHistogram.fromInput.clear();
    await numberHistogram.fromInput.pressSequentially('2');
    await expect(numberHistogram.rangeStartAfterEndError).toBeVisible();
    await expect(numberHistogram.rangeEndBeforeStartError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });
});
test.describe('Gene scores categorical histogram tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore(
      'SFARI Gene Score - Evidence strength supporting a gene\'s association with autism'
    );
  });

  test('should switch historgam selection modes', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.openMode();
    await expect(categoricalHistogram.menuContent.getByRole('menuitem')).toHaveCount(3);
    await expect(categoricalHistogram.modeMenuItem('range selector')).toBeVisible();
    await expect(categoricalHistogram.modeMenuItem('click selector')).toBeVisible();
    await expect(categoricalHistogram.modeMenuItem('dropdown selector')).toBeVisible();

    await expect(categoricalHistogram.modeMenuItem('range selector')).toHaveCSS('background-color', 'rgb(42, 99, 149)');
    await expect(categoricalHistogram.rangeSelectorLines).toHaveCount(2);

    await categoricalHistogram.modeMenuItem('click selector').click();
    await expect(categoricalHistogram.rangeSelectorLines).toHaveCount(0);

    await categoricalHistogram.openMode();
    await expect(categoricalHistogram.modeMenuItem('click selector')).toHaveCSS('background-color', 'rgb(42, 99, 149)');

    await categoricalHistogram.modeMenuItem('dropdown selector').click();
    await categoricalHistogram.openMode();
    await expect(categoricalHistogram.modeMenuItem('dropdown selector'))
      .toHaveCSS('background-color', 'rgb(42, 99, 149)');

    await expect(page.locator('[gpf-categorical-histogram]')).not.toBeVisible();
  });

  test('should check switch selection mode button is not visible for other histograms', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneScores = genotypeBrowser.genes.geneScores;
    await expect(geneScores.categorical.root).toBeVisible();
    await expect(geneScores.categorical.modeButton).toBeVisible();
    await expect(geneScores.numberHistogram.fromInput).not.toBeVisible();
    await expect(geneScores.numberHistogram.toInput).not.toBeVisible();

    await geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');
    await expect(geneScores.categorical.modeButton).not.toBeVisible();
    await expect(geneScores.numberHistogram.root).toBeVisible();
  });

  test('should check historgam colors change in range selector mode', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await categoricalHistogram.rangeSelectorLines.nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(1000, 400, {steps: 3});
    await page.mouse.up();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');


    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(100, 400, {steps: 3});
    await page.mouse.up();

    await categoricalHistogram.rangeSelectorLines.nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(1200, 400, {steps: 3});
    await page.mouse.up();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check historgam colors change in click selector mode', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');
    await expect(categoricalHistogram.pleaseSelectValueHint).toBeVisible();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await categoricalHistogram.bar('1').click();
    await expect(categoricalHistogram.pleaseSelectValueHint).not.toBeVisible();
    await categoricalHistogram.bar('2').click();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await categoricalHistogram.bar('1').click();
    await categoricalHistogram.bar('2').click();

    await expect(categoricalHistogram.pleaseSelectValueHint).toBeVisible();
    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should check if range selection is reset when switching to click selection', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await categoricalHistogram.selectMode('click selector');
    await categoricalHistogram.selectMode('range selector');

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check if click selection is reset when switching to range selection', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');

    await categoricalHistogram.bar('3').click();
    await categoricalHistogram.bar('2').click();

    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await categoricalHistogram.selectMode('range selector');
    await categoricalHistogram.selectMode('click selector');

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should check if range selection is reset when selecting other histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneScores = genotypeBrowser.genes.geneScores;
    const categoricalHistogram = geneScores.categorical;
    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');

    await geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');
    await geneScores.selectScore('SFARI Gene Score - Evidence strength supporting a gene\'s association with autism');

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check if click selection is reset when selecting other histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneScores = genotypeBrowser.genes.geneScores;
    const categoricalHistogram = geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');

    await categoricalHistogram.bar('1').click();

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(70, 130, 180)');

    await geneScores.selectScore('RVIS - Intolerance of a gene to genetic variants');
    await geneScores.selectScore('SFARI Gene Score - Evidence strength supporting a gene\'s association with autism');

    await categoricalHistogram.selectMode('click selector');

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should set ranges and share query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should set ranges and download', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('fixtures/gene-scores/variants1.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should set ranges and check table results', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.rangeSelectorLines.nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('18 variants selected');
  });

  test('should click histogram bars and share query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');
    await categoricalHistogram.bar('2').click();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(categoricalHistogram.bar('1')).toHaveCSS('fill', 'rgb(176, 196, 222)');
    await expect(categoricalHistogram.bar('2')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(categoricalHistogram.bar('3')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should click histogram bars and download', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');
    await categoricalHistogram.bar('3').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('fixtures/gene-scores/variants2.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should click histogram bars and check table results', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');
    await categoricalHistogram.bar('3').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('0 variants selected');
  });

  test('should select values from dropdown and validate', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('dropdown selector');

    await expect(categoricalHistogram.pleaseSelectValueHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();

    await categoricalHistogram.searchBox.click();
    await categoricalHistogram.matOption('2 (706)').click();

    await expect(categoricalHistogram.pleaseSelectValueHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();

    await expect(categoricalHistogram.valueWrapper).toBeVisible();
    await expect(categoricalHistogram.removeValue).toBeVisible();
    await expect(categoricalHistogram.valueWrapper).toContainText('2 (706)');

    await categoricalHistogram.searchBox.click();
    await expect(categoricalHistogram.matOptionHasText('2 (706)')).toBeDisabled();
  });

  test('should remove selected value from list of values and validate', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('dropdown selector');

    await categoricalHistogram.searchBox.focus();
    await page.keyboard.type('3');
    await expect(categoricalHistogram.matOption('2 (706)')).not.toBeVisible();
    await categoricalHistogram.matOption('3 (143)').click();

    await categoricalHistogram.searchBox.click();
    await categoricalHistogram.matOption('1 (233)').click();

    await expect(categoricalHistogram.valuesList).toContainText('3 (143)');
    await expect(categoricalHistogram.valuesList).toContainText('1 (233)');
    await expect(categoricalHistogram.removeValue).toHaveCount(2);

    await categoricalHistogram.removeValue.nth(0).click();
    await categoricalHistogram.removeValue.nth(0).click();

    await categoricalHistogram.searchBox.click();
    await expect(categoricalHistogram.matOptionHasText('1 (233)')).toBeEnabled();
    await expect(categoricalHistogram.matOptionHasText('3 (143)')).toBeEnabled();

    await expect(categoricalHistogram.pleaseSelectValueHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
  });

  test('errors state reset when validation fails and switch tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('click selector');

    await expect(categoricalHistogram.root).toBeVisible();
    await expect(categoricalHistogram.pleaseSelectValueHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();

    await genotypeBrowser.openToolLink('Gene browser');

    await genotypeBrowser.openToolLink('Genotype browser');

    await expect(categoricalHistogram.root).not.toBeVisible();
    await expect(categoricalHistogram.pleaseSelectValueHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
  });

  test('should check save/share query when using dropdown selector', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('dropdown selector');

    await categoricalHistogram.searchBox.click();
    await categoricalHistogram.matOption('3 (143)').click();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(categoricalHistogram.searchBox).toBeEmpty();
    await expect(categoricalHistogram.valueWrapper).toHaveCount(1);
    await expect(categoricalHistogram.valuesList).toContainText('3 (143)');
  });

  test('should check downloading when using dropdown selector', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('dropdown selector');

    await categoricalHistogram.searchBox.click();
    await categoricalHistogram.matOption('3 (143)').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('fixtures/gene-scores/variants3.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check table preview when using dropdown selector', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await categoricalHistogram.selectMode('dropdown selector');

    await categoricalHistogram.searchBox.click();
    await categoricalHistogram.matOption('3 (143)').click();

    await genotypeBrowser.runTablePreview();

    await expect(genotypeBrowser.variantsCount).toHaveText('0 variants selected');
  });
});
