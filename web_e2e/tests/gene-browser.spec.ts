// cypress/integration/example.spec.ts
import { test, expect, Page, Locator } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';
import * as fs from 'fs';

test.describe('Gene browser basic display tests before query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
  });

  test('should display "Gene Symbol" card title', async({ page }) => {
    await expect(page.getByText('Gene Symbol')).toBeVisible();
  });

  test('should display search box', async({ page }) => {
    await expect(page.locator('gpf-gene-browser input#search-box')).toBeVisible();
  });

  test('should display the "Coding only" checkbox', async({ page }) => {
    await expect(page.locator('input#coding-only-checkbox')).toBeVisible();
  });

  test('should display the "Go" button', async({ page }) => {
    await expect(page.locator('input[value=\'Go\']')).toBeVisible();
  });

  test('should NOT display the filters', async({ page }) => {
    await expect(page.locator('#filters')).not.toBeVisible();
  });

  test('should NOT display the gene plot', async({ page }) => {
    await expect(page.locator('gpf-gene-plot')).not.toBeVisible();
  });

  test('should NOT display the genotype preview table', async({ page }) => {
    await expect(page.locator('gpf-genotype-preview-table')).not.toBeVisible();
  });
});

test.describe('Gene browser basic display tests after query', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
    await page.getByPlaceholder('Search gene').pressSequentially('chd8');
    await page.getByRole('button', { name: 'Go' }).click();
    await expect(page.locator('gpf-genotype-preview-table')).toBeVisible();
  });

  test('should display the filters', async({ page }) => {
    await expect(page.locator('#filters')).toBeVisible();
  });

  test('should display the gene plot', async({ page }) => {
    await expect(page.locator('gpf-gene-plot')).toBeVisible();
  });

  test('should display the genotype preview table', async({ page }) => {
    await expect(page.locator('gpf-genotype-preview-table')).toBeVisible();
  });


  test('should have Affected status checkboxes', async({ page }) => {
    await expect(getAffectedStatusFilter(page, 'Affected only')).toBeVisible();
    await expect(getAffectedStatusFilter(page, 'Unaffected only')).toBeVisible();
    await expect(getAffectedStatusFilter(page, 'Affected and unaffected')).toBeVisible();
  });

  test('should have effect types checkboxes', async({ page }) => {
    await expect(getEffectTypesFilter(page, 'LGDs')).toBeVisible();
    await expect(getEffectTypesFilter(page, 'missense')).toBeVisible();
    await expect(getEffectTypesFilter(page, 'synonymous')).toBeVisible();
    await expect(getEffectTypesFilter(page, 'CNV+')).toBeVisible();
    await expect(getEffectTypesFilter(page, 'CNV-')).toBeVisible();
    await expect(getEffectTypesFilter(page, 'Other')).toBeVisible();
  });

  test('should have effect types checkboxes', async({ page }) => {
    await expect(getInheritanceTypesFilter(page, 'Denovo')).toBeVisible();
    await expect(getInheritanceTypesFilter(page, 'Transmitted')).toBeVisible();
  });

  test('should have variant types checkboxes', async({ page }) => {
    await expect(getVariantTypesFilter(page, 'del')).toBeVisible();
    await expect(getVariantTypesFilter(page, 'ins')).toBeVisible();
    await expect(getVariantTypesFilter(page, 'del')).toBeVisible();
    await expect(getVariantTypesFilter(page, 'CNV+')).toBeVisible();
    await expect(getVariantTypesFilter(page, 'CNV-')).toBeVisible();
  });

  test('should have family variants count', async({ page }) => {
    await expect(page.locator('span#family-variants-count')).toBeVisible();
  });

  test('should have download family varinats button', async({ page }) => {
    await expect(page.locator('#download-family-variants-button')).toBeVisible();
  });

  test('should go to chd8 gene page, filter out Affected only ' +
  'family variants and check if download button is disabled', async({ page }) => {
    await getAffectedStatusFilter(page, 'Affected only').click();
    await expect(page.locator('#download-family-variants-button')).toBeDisabled();
  });
});

test.describe('Gene browser download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
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
    test('should go to ' + gene + ' gene page, filter out ' + filtersToUncheck.toString() +
              'family variants and compare the files to the reference data', async({ page }) => {
      await page.locator('#search-box').pressSequentially(gene);
      await page.locator('#search-box').press('Enter');

      await getAnyFilter(page, filtersToUncheck[0].field, filtersToUncheck[0].filter).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');
      await getAnyFilter(page, filtersToUncheck[1].field, filtersToUncheck[1].filter).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');

      const downloadPromise = page.waitForEvent('download');
      await page.locator('#download-family-variants-button').click();
      const downloadedFile = await downloadPromise;

      const streamData = downloadedFile.createReadStream();
      const data = [];

      for await (const chunk of await streamData) {
        data.push(chunk);
      }

      const expectedVariantsPath = path.join(__dirname + '/../fixtures/gene-browser/' + expectedPath);
      const expectedFileLines = fs.readFileSync(expectedVariantsPath, 'utf8');
      const downloadedData = Buffer.concat(data);
      expect(downloadedData.toString()).toEqual(expectedFileLines);
    });
  });
});

function getAffectedStatusFilter(page: Page, affectedStatusCheckbox: string): Locator {
  return page.getByLabel(affectedStatusCheckbox, { exact: true });
}

function getEffectTypesFilter(page: Page, effectTypesCheckbox: string): Locator {
  return page.locator('#effect-types-filters').getByText(effectTypesCheckbox, { exact: true });
}

function getInheritanceTypesFilter(page: Page, inheritanceTypesCheckbox: string): Locator {
  return page.locator('#inheritance-types-filters').getByText(inheritanceTypesCheckbox);
}

function getVariantTypesFilter(page: Page, variantTypeCheckbox: string): Locator {
  return page.locator('#variant-types-filters').getByText(variantTypeCheckbox);
}

function getAnyFilter(page: Page, field: string, filterName: string): Locator {
  switch (field) {
    case 'variantTypes':
      return getVariantTypesFilter(page, filterName);
    case 'affectedStatus':
      return getAffectedStatusFilter(page, filterName);
    case 'inheritanceTypes':
      return getInheritanceTypesFilter(page, filterName);
    case 'effectTypes':
      return getEffectTypesFilter(page, filterName);
    default:
      return null;
  }
}