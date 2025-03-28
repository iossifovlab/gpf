import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { datasetIds } from './utils';

test.describe('Gene plot tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Gene browser');
    await page.locator('gpf-gene-browser input#search-box').pressSequentially('chd8');
    await page.locator('input[value=\'Go\']').click();
  });

  test('should check gene plot header', async({ page }) => {
    await expect(page.locator('#undo-button')).toBeVisible();
    await expect(page.locator('#redo-button')).toBeVisible();
    await expect(page.locator('#reset-button')).toBeVisible();
    await expect(page.locator('#variants-count-span')).toBeVisible();
    await expect(page.getByText('Hide transcripts')).toBeVisible();
    await expect(page.getByText('Condense introns')).toBeVisible();
    await expect(page.locator('#gene-title')).toBeVisible();
    await expect(page.locator('#gene-title')).toHaveText('CHD8');
    await expect(page.locator('#summary-alleles-count span')).toBeVisible();
    await expect(page.locator('#download-summary-variants-button')).toBeVisible();
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
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');
      await expect(page.locator('#variants-count-span')).toHaveText('8 variants selected');

      await page.locator('#affected-status-filters').getByLabel(data.checkbox, {exact: true}).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(data.expectedSummaryAllelesCount);
      await expect(page.locator('#variants-count-span')).toHaveText(data.expectedVariantsCount);

      await page.locator('#affected-status-filters').getByLabel(data.checkbox, {exact: true}).click();
    });
  });

  [
    {checkbox: 'missense', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Other', expectedSummaryAllelesCount: '7 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with effect type'+ data.checkbox, async({ page }) => {
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');
      await expect(page.locator('#variants-count-span')).toHaveText('8 variants selected');

      await page.locator('#effect-types-filters').getByText(data.checkbox, {exact: true}).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(data.expectedSummaryAllelesCount);

      await page.locator('#effect-types-filters').getByText(data.checkbox, {exact: true}).click();
    });
  });

  [
    {checkbox: 'Denovo', expectedSummaryAllelesCount: '0 / 8'},
    {checkbox: 'Transmitted', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with inheritance type '+ data.checkbox, async({ page }) => {
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');
      await expect(page.locator('#variants-count-span')).toHaveText('8 variants selected');

      await page.locator('#inheritance-types-filters').getByText(data.checkbox, {exact: true}).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(data.expectedSummaryAllelesCount);

      await page.locator('#inheritance-types-filters').getByText(data.checkbox, {exact: true}).click();
    });
  });

  [
    {checkbox: 'sub', expectedSummaryAllelesCount: '5 / 8'},
    {checkbox: 'ins', expectedSummaryAllelesCount: '7 / 8'},
    {checkbox: 'del', expectedSummaryAllelesCount: '4 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    test('should display the correct value when filtering with varint type '+ data.checkbox, async({ page }) => {
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');
      await expect(page.locator('#variants-count-span')).toHaveText('8 variants selected');

      await page.locator('#variant-types-filters').getByLabel(data.checkbox, {exact: true}).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(data.expectedSummaryAllelesCount);

      await page.locator('#variant-types-filters').getByLabel(data.checkbox, {exact: true}).click();
    });
  });
});

test.describe('Gene plot download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Gene browser');
  });

  test('should go to chd8 gene page, filter out Affected only ' +
        'summary variants and check if download button is disabled', async({ page }) => {
    await page.locator('gpf-gene-browser input#search-box').pressSequentially('chd8');
    await page.locator('input[value=\'Go\']').click();
    await page.locator('#affected-status-filters').getByLabel('Affected only', {exact: true}).click();
    await expect(page.getByTitle('Download summary variants')).toBeDisabled();
  });

  const testCases = [
    {
      gene: 'chd8',
      filtersToUncheck: [{ field: '#effect-types-filters', filter: 'Other'},
        { field: '#variant-types-filters', filter: 'ins'}],
      expectedPath: 'summary_variants1.tsv'
    },
    {
      gene: 'pogz',
      filtersToUncheck: [{ field: '#effect-types-filters', filter: 'missense'},
        { field: '#effect-types-filters', filter: 'synonymous'}],
      expectedPath: 'summary_variants2.tsv'
    }
  ];
  testCases.forEach(testCase => {
    test('should go to '
       + testCase.gene + ' gene page, filter out ' + testCase.filtersToUncheck[0].filter
       + ', ' + testCase.filtersToUncheck[1].filter +
          'summary variants and compare the files to the reference data', async({ page }
    ) => {
      await page.locator('gpf-gene-browser input#search-box').pressSequentially(testCase.gene);
      await page.locator('input[value=\'Go\']').click();

      await page.locator(testCase.filtersToUncheck[0].field)
        .getByText(testCase.filtersToUncheck[0].filter, {exact: true}).click();
      await page.locator(testCase.filtersToUncheck[1].field)
        .getByText(testCase.filtersToUncheck[1].filter, {exact: true}).click();

      const downloadedVariants = page.waitForEvent('download');
      await page.getByTitle('Download summary variants').click();

      const download = await downloadedVariants;
      const fixtureData = scanCSV(await download.path(), {sep: '\t'});
      const downloadData = scanCSV('playwright/fixtures/gene-browser/' + testCase.expectedPath, {sep: '\t'});
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('location');
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('location');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });
});
