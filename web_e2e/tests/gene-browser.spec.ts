import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { GeneBrowser } from './components/gene-browser.component';

test.describe('Gene browser basic display tests before query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
  });

  test('should check if elements in Gene Symbol are shown before query', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await expect(geneBrowser.geneSymbolLabel).toBeVisible();
    await expect(geneBrowser.searchBox).toBeVisible();
    await expect(geneBrowser.codingOnlyCheckbox).toBeVisible();
    await expect(geneBrowser.goInput).toBeVisible();
    await expect(geneBrowser.filters).not.toBeVisible();
    await expect(geneBrowser.genePlot).not.toBeVisible();
    await expect(geneBrowser.previewTable).not.toBeVisible();
  });
});

test.describe('Gene browser basic display tests after query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Gene browser');
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.searchBox.pressSequentially('chd8');
    await geneBrowser.goRoleButton.click();
    await expect(geneBrowser.previewTable).toBeVisible();
  });

  test('should check if elements in Gene Symbol are shown after query', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await expect(geneBrowser.filters).toBeVisible();
    await expect(geneBrowser.genePlot).toBeVisible();
    await expect(geneBrowser.previewTable).toBeVisible();
    await expect(geneBrowser.affectedStatusFilter('Affected only')).toBeVisible();
    await expect(geneBrowser.affectedStatusFilter('Unaffected only')).toBeVisible();
    await expect(geneBrowser.affectedStatusFilter('Affected and unaffected')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('LGDs')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('missense')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('synonymous')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('CNV+')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('CNV-')).toBeVisible();
    await expect(geneBrowser.effectTypesFilter('Other')).toBeVisible();
    await expect(geneBrowser.inheritanceTypesFilter('Denovo')).toBeVisible();
    await expect(geneBrowser.inheritanceTypesFilter('Transmitted')).toBeVisible();
    await expect(geneBrowser.variantTypesFilter('del')).toBeVisible();
    await expect(geneBrowser.variantTypesFilter('ins')).toBeVisible();
    await expect(geneBrowser.variantTypesFilter('del')).toBeVisible();
    await expect(geneBrowser.variantTypesFilter('CNV+')).toBeVisible();
    await expect(geneBrowser.variantTypesFilter('CNV-')).toBeVisible();
    await expect(geneBrowser.familyVariantsCountBadge).toBeVisible();
    await expect(geneBrowser.downloadFamilyVariantsButton).toBeVisible();
  });

  test('should go to chd8 gene page, filter out Affected only ' +
  'family variants and check if download button is disabled', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.affectedStatusFilter('Affected only').click();
    await expect(geneBrowser.downloadFamilyVariantsButton).toBeDisabled();
  });
});

test.describe('Gene browser family alleles count and table tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Gene browser');
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.searchBox.pressSequentially('chd8');
    await geneBrowser.goRoleButton.click();
    await expect(geneBrowser.previewTable).toBeVisible();
  });

  [
    { checkbox: 'Affected only', type: 'affectedStatus', expectedFamilyAllelesCount: '0 / 8' },
    { checkbox: 'Unaffected only', type: 'affectedStatus', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'Affected and unaffected', type: 'affectedStatus', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'LGDs', type: 'effectTypes', expectedFamilyAllelesCount: '1 / 8' },
    { checkbox: 'missense', type: 'effectTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'synonymous', type: 'effectTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'CNV+', type: 'effectTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'CNV-', type: 'effectTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'Other', type: 'effectTypes', expectedFamilyAllelesCount: '7 / 8' },
    { checkbox: 'Denovo', type: 'inheritanceTypes', expectedFamilyAllelesCount: '0 / 8' },
    { checkbox: 'Transmitted', type: 'inheritanceTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'sub', type: 'variantTypes', expectedFamilyAllelesCount: '5 / 8' },
    { checkbox: 'ins', type: 'variantTypes', expectedFamilyAllelesCount: '7 / 8' },
    { checkbox: 'del', type: 'variantTypes', expectedFamilyAllelesCount: '4 / 8' },
    { checkbox: 'CNV+', type: 'variantTypes', expectedFamilyAllelesCount: '8 / 8' },
    { checkbox: 'CNV-', type: 'variantTypes', expectedFamilyAllelesCount: '8 / 8' },
  ].forEach((testCase) => {
    test('should display the correct value when filtering with the "'
          + testCase.checkbox + '" checkbox and ' + testCase.type, async({ page }
    ) => {
      const geneBrowser = new GeneBrowser(page);
      await Promise.all([
        page.waitForRequest(utils.backendUrl + '/api/v3/genotype_browser/query'),
        geneBrowser.filter(testCase.type, testCase.checkbox).click(),
      ]);
      await expect(geneBrowser.familyVariantsCountSpan).toHaveText(testCase.expectedFamilyAllelesCount);
    });
  });

  test('should check table rows count', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await expect(geneBrowser.familyVariantsCount).toHaveText('8 / 8');
    await expect(geneBrowser.tableRows).toHaveCount(8);
  });

  test('should check table if nothing found is shown with filter Denovo', async({page }) => {
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.inheritanceTypesFilter('Denovo').click();
    await expect(geneBrowser.nothingFoundRow).toBeVisible();
    await expect(geneBrowser.familyVariantsCount).toHaveText('0 / 8');

    await geneBrowser.inheritanceTypesFilter('Denovo').click();

    await page.waitForResponse(
      resp => resp.url().includes('/api/v3/genotype_browser/query') && resp.status() === 200
    );

    await expect(geneBrowser.nothingFoundRow).not.toBeVisible();
  });

  test('should check table rows when sub, ins and CNV+ are unchecked', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    await geneBrowser.variantTypesFilter('sub').click();
    await geneBrowser.variantTypesFilter('ins').click();
    await geneBrowser.variantTypesFilter('CNV+').click();

    await expect(geneBrowser.familyVariantsCount).toHaveText('4 / 8');
    await expect(geneBrowser.tableRows).toHaveCount(4);
  });
});
test.describe('Gene browser download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Gene browser');
  });
  const tests = [
    {
      gene: 'chd8',
      filtersToUncheck: [{ field: 'effectTypes', filter: 'Other'},
        { field: 'variantTypes', filter: 'ins'}],
      expectedPath: 'variants1.tsv'
    },
    {
      gene: 'pogz',
      filtersToUncheck: [{ field: 'effectTypes', filter: 'missense'},
        { field: 'effectTypes', filter: 'synonymous'}],
      expectedPath: 'variants2.tsv'
    }
  ];
  tests.forEach(({ gene, filtersToUncheck, expectedPath }) => {
    test('should go to ' + gene + ' gene page, filter out '
        + filtersToUncheck[0].filter + ', ' + filtersToUncheck[1].filter +
              ' family variants and compare the files to the reference data', async({ page }) => {
      const geneBrowser = new GeneBrowser(page);
      await geneBrowser.searchBox.pressSequentially(gene);
      await geneBrowser.searchBox.press('Enter');

      await Promise.all([
        page.waitForRequest(utils.backendUrl + '/api/v3/genotype_browser/query'),
        geneBrowser.filter(filtersToUncheck[0].field, filtersToUncheck[0].filter).click(),
      ]);
      await Promise.all([
        page.waitForRequest(utils.backendUrl + '/api/v3/genotype_browser/query'),
        geneBrowser.filter(filtersToUncheck[1].field, filtersToUncheck[1].filter).click(),
      ]);

      const downloadPromise = page.waitForEvent('download');
      await geneBrowser.downloadFamilyVariantsButton.click();
      const downloadedFile = await downloadPromise;

      const fixtureData = scanCSV(await downloadedFile.path(), {sep: '\t'});
      const downloadData = scanCSV('fixtures/gene-browser/' + expectedPath, {sep: '\t'});
      const fixtureFrame = await fixtureData.collect();
      const downloadFrame = await downloadData.collect();
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });
});
