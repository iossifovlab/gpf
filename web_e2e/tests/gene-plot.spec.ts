import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { datasetIds } from './utils';
import { GeneBrowser } from './components/gene-browser.component';

test.describe('Gene plot tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Gene browser');
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.searchBox.pressSequentially('chd8');
    await geneBrowser.goInput.click();
  });

  test('should check gene plot header', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await expect(geneBrowser.undoButton).toBeVisible();
    await expect(geneBrowser.redoButton).toBeVisible();
    await expect(geneBrowser.resetButton).toBeVisible();
    await expect(geneBrowser.variantsCountSpan).toBeVisible();
    await expect(geneBrowser.hideTranscripts).toBeVisible();
    await expect(geneBrowser.condenseIntrons).toBeVisible();
    await expect(geneBrowser.geneTitle).toBeVisible();
    await expect(geneBrowser.geneTitle).toHaveText('CHD8');
    await expect(geneBrowser.summaryAllelesCountSpan).toBeVisible();
    await expect(geneBrowser.downloadSummaryVariantsButton).toBeVisible();
  });

  [
    {checkbox: 'Affected only', expectedSummaryAllelesCount: '0 / 8', expectedVariantsCount: '0 variants selected'},
    {checkbox: 'Unaffected only', expectedSummaryAllelesCount: '8 / 8', expectedVariantsCount: '8 variants selected'},
    {
      checkbox: 'Affected and unaffected', expectedSummaryAllelesCount: '8 / 8',
      expectedVariantsCount: '8 variants selected'
    }
  ].forEach(data => {
    test('should display the correct value when filtering with affected status ' + data.checkbox, async({ page }) => {
      const geneBrowser = new GeneBrowser(page);
      await expect(geneBrowser.summaryAllelesCount).toHaveText('8 / 8');
      await expect(geneBrowser.variantsCountSpan).toHaveText('8 variants selected');

      await geneBrowser.affectedStatusFilterExact(data.checkbox).click();
      await expect(geneBrowser.summaryAllelesCount).toHaveText(data.expectedSummaryAllelesCount);
      await expect(geneBrowser.variantsCountSpan).toHaveText(data.expectedVariantsCount);

      await geneBrowser.affectedStatusFilterExact(data.checkbox).click();
    });
  });

  [
    {checkbox: 'missense', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Other', expectedSummaryAllelesCount: '7 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with effect type'+ data.checkbox, async({ page }) => {
      const geneBrowser = new GeneBrowser(page);
      await expect(geneBrowser.summaryAllelesCount).toHaveText('8 / 8');
      await expect(geneBrowser.variantsCountSpan).toHaveText('8 variants selected');

      await geneBrowser.effectTypesFilterExact(data.checkbox).click();
      await expect(geneBrowser.summaryAllelesCount).toHaveText(data.expectedSummaryAllelesCount);

      await geneBrowser.effectTypesFilterExact(data.checkbox).click();
    });
  });

  [
    {checkbox: 'Denovo', expectedSummaryAllelesCount: '0 / 8'},
    {checkbox: 'Transmitted', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with inheritance type '+ data.checkbox, async({ page }) => {
      const geneBrowser = new GeneBrowser(page);
      await expect(geneBrowser.summaryAllelesCount).toHaveText('8 / 8');
      await expect(geneBrowser.variantsCountSpan).toHaveText('8 variants selected');

      await geneBrowser.inheritanceTypesFilterExact(data.checkbox).click();
      await expect(geneBrowser.summaryAllelesCount).toHaveText(data.expectedSummaryAllelesCount);

      await geneBrowser.inheritanceTypesFilterExact(data.checkbox).click();
    });
  });

  [
    {checkbox: 'sub', expectedSummaryAllelesCount: '5 / 8'},
    {checkbox: 'ins', expectedSummaryAllelesCount: '7 / 8'},
    {checkbox: 'del', expectedSummaryAllelesCount: '4 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with varint type '+ data.checkbox, async({ page }) => {
      const geneBrowser = new GeneBrowser(page);
      await expect(geneBrowser.summaryAllelesCount).toHaveText('8 / 8');
      await expect(geneBrowser.variantsCountSpan).toHaveText('8 variants selected');

      await geneBrowser.variantTypesFilterExact(data.checkbox).click();
      await expect(geneBrowser.summaryAllelesCount).toHaveText(data.expectedSummaryAllelesCount);

      await geneBrowser.variantTypesFilterExact(data.checkbox).click();
    });
  });
});

test.describe('Gene plot download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Gene browser');
  });

  test('should go to chd8 gene page, filter out Affected only ' +
        'summary variants and check if download button is disabled', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.searchBox.pressSequentially('chd8');
    await geneBrowser.goInput.click();
    await geneBrowser.affectedStatusFilterExact('Affected only').click();
    await expect(geneBrowser.downloadSummaryVariantsTitle).toBeDisabled();
  });

  const testCases = [
    {
      gene: 'chd8',
      filtersToUncheck: [{ field: 'effectTypes', filter: 'Other'},
        { field: 'variantTypes', filter: 'ins'}],
      expectedPath: 'summary_variants1.tsv'
    },
    {
      gene: 'pogz',
      filtersToUncheck: [{ field: 'effectTypes', filter: 'missense'},
        { field: 'effectTypes', filter: 'synonymous'}],
      expectedPath: 'summary_variants2.tsv'
    }
  ];
  testCases.forEach(testCase => {
    test('should go to '
       + testCase.gene + ' gene page, filter out ' + testCase.filtersToUncheck[0].filter
       + ', ' + testCase.filtersToUncheck[1].filter +
          'summary variants and compare the files to the reference data', async({ page }
    ) => {
      const geneBrowser = new GeneBrowser(page);
      await geneBrowser.searchBox.pressSequentially(testCase.gene);
      await geneBrowser.goInput.click();

      await geneBrowser.panel(testCase.filtersToUncheck[0].field)
        .getByText(testCase.filtersToUncheck[0].filter, {exact: true}).click();
      await geneBrowser.panel(testCase.filtersToUncheck[1].field)
        .getByText(testCase.filtersToUncheck[1].filter, {exact: true}).click();

      const downloadedVariants = page.waitForEvent('download');
      await geneBrowser.downloadSummaryVariantsTitle.click();

      const download = await downloadedVariants;
      const fixtureData = scanCSV(await download.path(), {sep: '\t'});
      const downloadData = scanCSV('fixtures/gene-browser/' + testCase.expectedPath, {sep: '\t'});
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('location');
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('location');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });
});
