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

    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
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
    {study: datasetIds.helloWorldGenotypes, count: '10'},
    {study: datasetIds.denovoHelloWorld, count: '10'},
    {study: datasetIds.vcfHelloWorld, count: '15'},
    {study: datasetIds.iossifov2014Liftover, count: '8'},
    {study: datasetIds.multiLiftover, count: '0'}
  ].forEach(data => {
    test('should display the correct overview paragraph ' +
    'when gene symbol is "CHD8" at /' + data.study + '/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, data.study, 'Genotype browser');
      await page.getByRole('tab', {name: 'Gene symbols'}).click();
      await page.locator('#text-area').fill('CHD8');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {region: 'chr1:101806080-125000000', count: '7'},
    {region: 'chr1:1592000-15929267', count: '5'},
    {region: 'chrX:70000000-74000000', count: '2'}
  ].forEach(data => {
    test('should display the correct overview paragraph' +
    ' when regions filter is "' + data.region + '" at /iossifov_2014_liftover/browser', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
      await page.locator('#regions-filter').click();
      await page.locator('gpf-regions-filter textarea').focus();
      await page.keyboard.type(data.region);
      await page.waitForTimeout(1000);
      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {
      study: datasetIds.denovoHelloWorld,
      affectedStatus: 'affected',
      count: '61'
    },
    {
      study: datasetIds.vcfHelloWorld,
      affectedStatus: 'affected',
      count: '19'
    },
    {
      study: datasetIds.vcfHelloWorld,
      affectedStatus: 'unaffected',
      count: '27'
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
    {childGender: 'male', count: '406'},
    {childGender: 'female', count: '169'},
    {childGender: 'unspecified', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when ' +
        'child gender is ' + data.childGender, async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      await page.locator('gpf-gender').getByRole('button', {name: 'None'}).click();
      await page.locator(`[class="gender-icon ${data.childGender}"]`).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {variantType: 'sub', count: '273'},
    {variantType: 'ins', count: '87'},
    {variantType: 'del', count: '212'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph when only ' +
    data.variantType + ' variant type checkbox is checked', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');

      await page.locator('gpf-variant-types').getByRole('button', {name: 'None'}).click();
      await page.locator('gpf-variant-types').getByLabel(data.variantType, {exact: true}).click();

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(page.locator('#variants-count-span')).toHaveText(`${data.count} variants selected`);
    });
  });

  [
    {effectType: 'All', count: '27'},
    {effectType: 'LGDs', count: '0'},
    {effectType: 'Nonsynonymous', count: '11'},
    {effectType: 'Coding', count: '15'},
    {effectType: 'UTRs', count: '0'}
  ].forEach(data => {
    test('should display the correct data in overview paragraph' +
        ' where effect types are ' + data.effectType, async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');

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
      study: datasetIds.denovoHelloWorld,
      inheritanceType: 'denovo',
      count: '61'
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
    {familyId: 'f1', count: '28'},
    {familyId: 'f2', count: '23'},
    {familyId: 'f3', count: '0'},
  ].forEach(data => {
    test('should display the correct overview paragraph when family id is "' + data.familyId + '"', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');

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
    {familyId: 'f1', values: {age: '166.33975219726562', iq: '124.9118881225586'}},
    {familyId: 'f2', values: {age: '111.53800201416016', iq: '118.6941146850586'}},
  ].forEach(data => {
    test('should display the correct age and iq values in the measures column for "'
    + data.familyId + '" family', async({ page }) => {
      await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');

      await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

      await page.locator('#family-ids').click();
      await page.locator('gpf-family-ids textarea').fill(data.familyId);

      await page.getByRole('button', { name: 'Table Preview' }).click();
      await expect(
        page.locator('gpf-table-view-cell:nth-child(6) > div').nth(0)
      ).toContainText(data.values.age);

      await expect(
        page.locator('gpf-table-view-cell:nth-child(6) > div').nth(1)
      ).toContainText(data.values.iq);
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
    await expect(page.locator('#variants-count-span')).toHaveText('164 variants selected');
  });
});

test.describe('Genotype browser download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
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

    const baseUrl = 'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&position=';

    await page.waitForSelector('span:text("572 variants selected")');
    await page.locator('#sort-child').getByText('family id').click();

    await expect(
      page.locator('a').filter({ hasText: /^chr4:41746278$/ }).first()
    ).toHaveAttribute('href', baseUrl + 'chr4:41746278');


    await expect(
      page.locator('a').filter({ hasText: /^chr13:51374698$/ }).first()
    ).toHaveAttribute('href', baseUrl + 'chr13:51374698');
  });

  test('should show details', async({ page }) => {
    await page.getByRole('button', { name: 'Table Preview' }).click();
    await page.waitForSelector('span:text("572 variants selected")');
    await page.locator('#sort-child').getByText('family id').click();

    await page.getByText('Show details').first().click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('.modal-content > .details-header')).toHaveCount(2);
    await expect(page.locator('.modal-content > .details-header').nth(0)).toHaveText('Family id: 14699');
    await expect(page.locator('.modal-content > .details-header').nth(1)).toHaveText('Location: chr4:41746278');
    await expect(page.locator('.modal-content > .grid-container')).toBeVisible();
  });
});