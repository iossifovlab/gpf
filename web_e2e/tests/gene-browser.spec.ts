// cypress/integration/example.spec.ts
import { test, expect, Page, Locator } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';

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

  test('should have inheritance types checkboxes', async({ page }) => {
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
    await expect(page.locator('.gene-plot')).toBeVisible();
  });

  test('should display the genotype preview table', async({ page }) => {
    await expect(page.locator('.genotype-preview-table')).toBeVisible();
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

  test('should have inheritance types checkboxes', async({ page }) => {
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
    await expect(page.locator('.family-alleles-count')).toBeVisible();
  });

  test('should have download family varinats button', async({ page }) => {
    await expect(page.locator('.download-family-variants-button')).toBeVisible();
  });
});

test.describe('Gene browser family alleles count and table tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
    await page.getByPlaceholder('Search gene').pressSequentially('chd8');
    await page.getByRole('button', { name: 'Go' }).click();
    await expect(page.locator('gpf-genotype-preview-table')).toBeVisible();
  });

  const testCases = [
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
  ];

  testCases.forEach((testCase) => {
    test('should display the correct value when filtering with the "'
          + testCase.checkbox + '" checkbox', async({ page }
    ) => {
      await getAnyFilter(page, testCase.type, testCase.checkbox).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');
      await expect(page.locator('#family-variants-count span')).toHaveText(testCase.expectedFamilyAllelesCount);
    });
  });

  test('should check table rows count', async({ page }) => {
    await expect(page.locator('#family-variants-count')).toHaveText('8 / 8');
    await expect(page.locator('.table-row')).toHaveCount(8);
  });

  test('should check table if nothing found is shown with filter Denovo', async({page }) => {
    await getInheritanceTypesFilter(page, 'Denovo').click();
    await expect(page.locator('#nothing-found-row')).toBeVisible();
    await expect(page.locator('#family-variants-count')).toHaveText('0 / 8');

    await getInheritanceTypesFilter(page, 'Denovo').click();
    await expect(page.locator('#nothing-found-row')).not.toBeVisible();
  });

  test('should check table rows when sub, ins and CNV+ are unchecked', async({ page }) => {
    await getVariantTypesFilter(page, 'sub').click();
    await getVariantTypesFilter(page, 'ins').click();
    await getVariantTypesFilter(page, 'CNV+').click();

    await expect(page.locator('#family-variants-count')).toHaveText('4 / 8');
    await expect(page.locator('.table-row')).toHaveCount(4);
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
    test('should go to ' + gene + ' gene page, filter out '
        + filtersToUncheck[0].filter + ', ' + filtersToUncheck[1].filter +
              ' family variants and compare the files to the reference data', async({ page }) => {
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
      const expectedFileLines = await utils.readFile(expectedVariantsPath);
      const downloadedData = Buffer.concat(data);
      expect(downloadedData.toString()).toEqual(expectedFileLines);
    });
  });
});

function getAffectedStatusFilter(page: Page, affectedStatusCheckbox: string): Locator {
  return page.locator('#affected-status-filters').getByLabel(affectedStatusCheckbox).nth(0);
}

function getEffectTypesFilter(page: Page, effectTypesCheckbox: string): Locator {
  return page.locator('#effect-types-filters').locator('span').getByText(effectTypesCheckbox).nth(0);
}

function getInheritanceTypesFilter(page: Page, inheritanceTypesCheckbox: string): Locator {
  return page.locator('#inheritance-types-filters').locator('span').getByText(inheritanceTypesCheckbox).nth(0);
}

function getVariantTypesFilter(page: Page, variantTypeCheckbox: string): Locator {
  return page.locator('#variant-types-filters').locator('span').getByText(variantTypeCheckbox).nth(0);
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


test.describe('Gene plot tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
    await page.locator('gpf-gene-browser input#search-box').pressSequentially('chd8');
    await page.locator('input[value=\'Go\']').click();
  });

  test('should have undo button', async({ page }) => {
    await expect(page.locator('#undo-button')).toBeVisible();
  });

  test('should have redo button', async({ page }) => {
    await expect(page.locator('#redo-button')).toBeVisible();
  });

  test('should have reset button', async({ page }) => {
    await expect(page.locator('#reset-button')).toBeVisible();
  });

  test('should have hide transcripts checkbox', async({ page }) => {
    await expect(page.getByText('Hide transcripts')).toBeVisible();
  });

  test('should have condense introns checkbox', async({ page }) => {
    await expect(page.getByText('Condense introns')).toBeVisible();
  });

  test('should have gene title with the correct text inside', async({ page }) => {
    await expect(page.locator('#gene-title')).toHaveText('CHD8');
  });

  test('should have summary alleles count field', async({ page }) => {
    await expect(page.locator('#summary-alleles-count')).toBeVisible();
  });

  test('should have summary download button', async({ page }) => {
    await expect(page.locator('#download-summary-variants-button')).toBeVisible();
  });
});

test.describe('Gene plot summary alleles count tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
    await page.locator('gpf-gene-browser input#search-box').pressSequentially('chd8');
    await page.locator('input[value=\'Go\']').click();
  });

  const testCases = [
    {checkbox: 'Affected only', expectedSummaryAllelesCount: '0 / 8', expectedVariantsCount: '0 variants selected'},
    {checkbox: 'Unaffected only', expectedSummaryAllelesCount: '8 / 8', expectedVariantsCount: '8 variants selected'},
    {
      checkbox: 'Affected and unaffected', expectedSummaryAllelesCount: '8 / 8',
      expectedVariantsCount: '8 variants selected'
    }
  ];

  testCases.forEach((testCase) => {
    test('should display the correct value when filtering with the "'
        + testCase.checkbox + '" checkbox', async({ page }
    ) => {
      await expect(getAffectedStatusFilter(page, testCase.checkbox)).toBeVisible();
      await expect(page.locator('span#summary-alleles-count')).toHaveText('8 / 8');
      await expect(page.locator('span#variants-count-span')).toHaveText('8 variants selected');

      await getAffectedStatusFilter(page, testCase.checkbox).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');
      await expect(page.locator('span#summary-alleles-count')).toHaveText(testCase.expectedSummaryAllelesCount);
      await expect(page.locator('span#variants-count-span')).toHaveText(testCase.expectedVariantsCount);
    });
  });


  const effectTypesTestCases = [
    {checkbox: 'LGDs', expectedSummaryAllelesCount: '1 / 8'},
    {checkbox: 'missense', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'synonymous', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV+', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Other', expectedSummaryAllelesCount: '7 / 8'}
  ];
  effectTypesTestCases.forEach(testCase => {
    test('should display the correct value when filtering with the "'
    + testCase.checkbox + '" checkbox', async({ page }
    ) => {
      await expect(page.locator('#effect-types-filters')).toBeVisible();
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');

      await getEffectTypesFilter(page, testCase.checkbox).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(testCase.expectedSummaryAllelesCount);
    });
  });

  const inheritanceTypesTestCases = [
    {checkbox: 'Denovo', expectedSummaryAllelesCount: '0 / 8'},
    {checkbox: 'Transmitted', expectedSummaryAllelesCount: '8 / 8'}
  ];

  inheritanceTypesTestCases.forEach(testCase => {
    test('should display the correct value when filtering with the "'
     + testCase.checkbox + '" checkbox', async({ page }
    ) => {
      await expect(page.locator('#inheritance-types-filters')).toBeVisible();
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');

      await getInheritanceTypesFilter(page, testCase.checkbox).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(testCase.expectedSummaryAllelesCount);
    });
  });

  const variantTypesTestCases = [
    {checkbox: 'sub', expectedSummaryAllelesCount: '5 / 8'},
    {checkbox: 'ins', expectedSummaryAllelesCount: '7 / 8'},
    {checkbox: 'del', expectedSummaryAllelesCount: '4 / 8'},
    {checkbox: 'CNV+', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'}
  ];

  variantTypesTestCases.forEach(testCase => {
    test('should display the correct value when filtering with the "'
    + testCase.checkbox + '" checkbox', async({ page }
    ) => {
      await expect(page.locator('#variant-types-filters')).toBeVisible();
      await expect(page.locator('#summary-alleles-count')).toHaveText('8 / 8');

      await getVariantTypesFilter(page, testCase.checkbox).click();
      await expect(page.locator('#summary-alleles-count')).toHaveText(testCase.expectedSummaryAllelesCount);

      await getVariantTypesFilter(page, testCase.checkbox).click();
    });
  });
});

test.describe('Gene plot download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
  });

  test('should go to chd8 gene page, filter out Affected only ' +
      'summary variants and check if download button is disabled', async({ page }) => {
    await page.locator('gpf-gene-browser input#search-box').pressSequentially('chd8');
    await page.locator('input[value=\'Go\']').click();
    await getAffectedStatusFilter(page, 'Affected only').click();
    await expect(page.getByTitle('Download summary variants')).toBeDisabled();
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
      await page.locator('gpf-gene-browser input#search-box').pressSequentially(testCase.gene);
      await page.locator('input[value=\'Go\']').click();

      await getAnyFilter(page, testCase.filtersToUncheck[0].field, testCase.filtersToUncheck[0].filter).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');
      await getAnyFilter(page, testCase.filtersToUncheck[1].field, testCase.filtersToUncheck[1].filter).click();
      await page.waitForRequest(utils.instanceUrl + '/api/v3/genotype_browser/query');

      const downloadedVariants = page.waitForEvent('download');
      await page.getByTitle('Download summary variants').click();
      const downloadedData = (await downloadedVariants).createReadStream();
      const compiledDownloadData = [];
      for await (const chunk of await downloadedData) {
        compiledDownloadData.push(chunk);
      }
      const expectedFile = await utils.readFile(
        path.join(__dirname + '/../fixtures/gene-browser/' + testCase.expectedPath)
      );

      expect(compiledDownloadData.toString()).toEqual(expectedFile);
    });
  });
});
