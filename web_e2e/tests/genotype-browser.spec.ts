import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Genotype browser tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
  });

  test('should display filters blocks and buttons', async({ page }) => {
    await expect(page.getByRole('button', { name: 'Table Preview' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Share/save query' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Download' })).toBeVisible();

    await expect(page.locator('gpf-regions-block')).toBeVisible();
    await expect(page.locator('gpf-genes-block')).toBeVisible();
    await expect(page.locator('gpf-genotype-block')).toBeVisible();
    await expect(page.locator('gpf-genomic-scores-block')).toBeVisible();
    await expect(page.locator('gpf-family-filters-block')).toBeVisible();
    await expect(page.locator('gpf-person-filters-block')).toBeVisible();
    await expect(page.locator('gpf-unique-family-variants-filter')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.compGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-unique-family-variants-filter')).toBeVisible();
  });

  test('should hide table preview results after changing a filter', async({ page }) => {
    await page.getByRole('button', { name: 'Table Preview' }).click();
    await expect(page.locator('gpf-genotype-preview-table')).toBeVisible();

    await page.locator('gpf-pedigree-selector').getByLabel('affected', {exact: true}).click();
    await expect(page.locator('gpf-genotype-preview-table')).not.toBeVisible();
  });
});

test.describe('Genotype browser table preview result tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });

  [
    {study: datasetIds.compAllLiftover, count: '30'},
    {study: datasetIds.compDenovoLiftover, count: '5'},
    {study: datasetIds.compVcfLiftover, count: '25'},
    {study: datasetIds.iossifov2014Liftover, count: '0'},
    {study: datasetIds.multiLiftover, count: '0'}
  ].forEach(data => {
    test('should display the correct overview paragraph ' +
    'when gene symbol is "SAMD11" at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');
      await page.getByRole('tab', {name: 'Gene symbols'}).click();
      await page.locator('#text-area').fill('SAMD11');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {region: '1:865627', count: '5'},
    {region: '1:865664', count: '3'},
    {region: '1:865691', count: '2'}
  ].forEach(data => {
    test('should display the correct overview paragraph' +
    ' when regions filter is "' + data.region + '" at /comp_vcf/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compVcfLiftover, 'Genotype browser');
      await page.locator('#regions-filter').click();
      await page.locator('gpf-regions-filter textarea').fill(data.region);

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.compAllLiftover,
      affectedStatus: 'affected',
      count: '30'
    },
    {
      study: datasetIds.compDenovoLiftover,
      affectedStatus: 'affected',
      count: '5'
    },
    {
      study: datasetIds.compVcfLiftover,
      affectedStatus: 'affected',
      count: '25'
    },
    {
      study: datasetIds.compDenovoLiftover,
      affectedStatus: 'unaffected',
      count: '0'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when ' +
    'affected status - ' + data.affectedStatus + ' is checked at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await page.locator('#pedigree-dropdown-menu-button').click();
      await page.locator('gpf-pedigree-selector').getByRole('link', { name: 'Affected Status' }).click();
      await page.locator('gpf-pedigree-selector').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-pedigree-selector').getByLabel(data.affectedStatus, {exact: true}).click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {childGender: 'male', count: '23'},
    {childGender: 'female', count: '22'},
    {childGender: 'unspecified', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when ' +
        'child gender is ' + data.childGender, async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compVcfLiftover, 'Genotype browser');

      await page.locator('gpf-gender').getByRole('button', {name: 'None'}).click();
      await page.locator(`[class="gender-icon ${data.childGender}"]`).click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {variantType: 'sub', count: '25'},
    {variantType: 'ins', count: '0'},
    {variantType: 'del', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when only ' +
    data.variantType + ' variant type checkbox is checked', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compVcfLiftover, 'Genotype browser');

      await page.locator('gpf-variant-types').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-variant-types').getByLabel(data.variantType, {exact: true}).click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {effectType: 'All', count: '25'},
    {effectType: 'LGDs', count: '0'},
    {effectType: 'Nonsynonymous', count: '12'},
    {effectType: 'Coding', count: '25'},
    {effectType: 'UTRs', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph' +
        ' where effect types are ' + data.effectType, async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compVcfLiftover, 'Genotype browser');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-effect-types').getByRole('button', {name: data.effectType}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.multiLiftover,
      inheritanceType: 'mendelian',
      count: '2'
    },
    {
      study: datasetIds.compAllLiftover,
      inheritanceType: 'denovo',
      count: '5'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when ' +
    'inheritance types are ' + data.inheritanceType + ' at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await page.locator('gpf-inheritancetypes').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-inheritancetypes').getByLabel(data.inheritanceType).click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {study: datasetIds.compDenovoLiftover, count: '5'},
    {study: datasetIds.compVcfLiftover, count: '0'}
  ].forEach(data => {
    test('should display the correct overview paragraph when ' +
    'inheritance types are denovo at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await page.locator('gpf-inheritancetypes').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-inheritancetypes').getByLabel('denovo').click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {familyId: 'f1', count: '4'},
    {familyId: 'f2', count: '5'},
    {familyId: 'f3', count: '4'},
    {familyId: 'f4', count: '6'},
  ].forEach(data => {
    test('should display the correct overview paragraph when family id is "' + data.familyId + '"', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compVcfLiftover, 'Genotype browser');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.locator('#family-ids').click();
      await page.locator('gpf-family-ids textarea').fill(data.familyId);

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'SCN2A',
      effectType: 'LGDs',
      overviewParagraph: '2 variants selected'
    },
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'NRXN1',
      effectType: 'LGDs',
      overviewParagraph: '1 variant selected'
    },
    {
      study: datasetIds.iossifov2014Liftover,
      geneSymbol: 'NRXN1',
      effectType: 'All',
      overviewParagraph: '1 variant selected'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when effect types are ' +
        data.effectType + ' and gene symbol is "' + data.geneSymbol +
        '" at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');

      await page.getByRole('tab', {name: 'Gene symbols'}).click();
      await page.locator('#text-area').fill(data.geneSymbol);

      await page.locator('gpf-effect-types').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-effect-types').getByRole('button', {name: data.effectType}).click();


      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(data.overviewParagraph);
    });
  });

  test('should display "2 variants selected" in overview paragraph ' +
  'when family id is 11002 at /iossifov_2014/browser', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();
    await page.locator('#family-ids').click();
    await page.locator('gpf-family-ids textarea').fill('11002');

    await page.getByRole('button', { name: 'Table Preview' }).click();
    await expect(page.locator('#variants-count-span')).toHaveText('2 variants selected');
  });

  test('should display "0 variants selected" in overview paragraph when the gene sets is ' +
  'GO Terms - GO:0016917 GABA_receptor_activity and effect type LGDs at /iossifov_2014/browser', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await page.locator('gpf-effect-types').getByRole('button', {name: 'LGDs'}).click();

    await page.locator('#gene-sets').click();
    await page.locator('#selected-collection').click();
    await page.locator('#selected-collection').selectOption('GO Terms');
    await page.locator('#search-box').click();
    await page.keyboard.type('GO:0016917');
    await page.waitForSelector('[title="GO:0016917 (22): GABA_receptor_activity"]');
    await page.getByText('GO:0016917 (22): GABA_receptor_activity').click();

    await page.getByRole('button', { name: 'Table Preview' }).click();
    await expect(page.locator('#variants-count-span')).toHaveText('0 variants selected');
  });

  [
    {
      effectTypes: ['missense'],
      count: '4'
    },
    {
      effectTypes: ['missense', 'synonymous'],
      count: '5'
    }
  ].forEach(data => {
    test('should display the correct overview paragraph when gene sets is GO Terms'+
    ' - GO:0016917 and effect types are ' + data.effectTypes.toString() +
    ' at /iossifov2014Liftover/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      await page.locator('#gene-sets').click();
      await page.locator('#selected-collection').click();
      await page.locator('#selected-collection').selectOption('GO Terms');
      await page.locator('#search-box').click();
      await page.keyboard.type('GO:0016917');
      await page.waitForSelector('[title="GO:0016917 (22): GABA_receptor_activity"]');
      await page.getByText('GO:0016917 (22): GABA_receptor_activity').click();

      await page.locator('gpf-effect-types').getByRole('button', {name: 'None'}).click();

      for (const type of data.effectTypes) {
        // eslint-disable-next-line no-await-in-loop
        await page.locator('gpf-effect-types').getByLabel(type).click();
      }

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {familyId: 'f1', values: {age: '166.339', iq: '104.911'}},
    {familyId: 'f2', values: {age: '111.538', iq: '66.694'}},
    {familyId: 'f3', values: {age: '68.001', iq: '69.333'}},
    {familyId: 'f4', values: {age: '157.618', iq: '103.074'}},
    {familyId: 'f5', values: {age: '171.890', iq: '38.885'}}
  ].forEach(data => {
    test('should display the correct age and iq values in the measures column for "'
    + data.familyId + '" family', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.compAllLiftover, 'Genotype browser');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.locator('#family-ids').click();
      await page.locator('gpf-family-ids textarea').fill(data.familyId);

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(
        page.locator('gpf-table-view-cell:nth-child(8) gpf-genotype-preview-field').first()
      ).toContainText(data.values.age);

      await expect(
        page.locator('gpf-table-view-cell:nth-child(8) gpf-genotype-preview-field').nth(2)
      ).toContainText(data.values.age);
    });
  });

  test('should display the correct overview paragraph with ' +
  'denovo inheritance types, affected only, 5\'UTR', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

    await page.locator('#pedigree-dropdown-menu-button').click();
    await page.locator('gpf-pedigree-selector').getByRole('link', { name: 'Affected Status' }).click();
    await page.locator('gpf-pedigree-selector').getByRole('button', {name: 'None'}).click();
    await page.locator('gpf-pedigree-selector').getByLabel('affected', {exact: true}).click();

    await page.locator('gpf-inheritancetypes').getByRole('button', {name: 'None'}).click();
    await page.locator('gpf-inheritancetypes').getByLabel('denovo').click();

    await page.locator('gpf-effect-types').getByRole('button', {name: 'None'}).click();
    await page.locator('gpf-effect-types').getByLabel('5\'UTR').click();

    await page.getByRole('button', { name: 'Table Preview' }).click();
    await expect(page.locator('#variants-count-span')).toHaveText('98 variants selected');
  });
});

test.describe('Genotype browser download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
  });

  test('should download all effect types CHD8 iossifov variants ' +
  'and validate whether they are equal to the reference data', async({ page }) => {
    await page.getByRole('tab', {name: 'Gene symbols'}).click();
    await page.locator('#text-area').fill('CHD8');

    await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', { name: 'Download' }).click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(await download.path(), { sep: '\t'});
    const downloadData = scanCSV('playwright/fixtures/genotype-browser/variants-1.tsv', { sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});


test.describe('Genotype browser table tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
  });

  test('should redirect to UCSC', async({ page }) => {
    await page.getByRole('button', { name: 'Table Preview' }).click();

    const baseUrl = 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr';

    await page.waitForSelector('span:text("569 variants selected")');
    await page.locator('#sort-child').getByText('family id').click();

    await expect(
      page.locator('a').filter({ hasText: /^4:41748295$/ }).first()
    ).toHaveAttribute('href', baseUrl + '4:41748295');


    await expect(
      page.locator('a').filter({ hasText: /^7:87339897$/ }).first()
    ).toHaveAttribute('href', baseUrl + '7:87339897');
  });

  test('should show details', async({ page }) => {
    await page.getByRole('button', { name: 'Table Preview' }).click();
    await page.waitForSelector('span:text("569 variants selected")');
    await page.locator('#sort-child').getByText('family id').click();

    await page.getByText('Show details').first().click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('.modal-content > .details-header')).toHaveCount(2);
    await expect(page.locator('.modal-content > .details-header').nth(0)).toHaveText('Family id: 14699');
    await expect(page.locator('.modal-content > .details-header').nth(1)).toHaveText('Location: 4:41748295');
    await expect(page.locator('.modal-content > .grid-container')).toBeVisible();
  });
});