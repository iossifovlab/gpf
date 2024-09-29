import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Pheno tool tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype tool');
  });

  test('should display pheno tool elements', async({ page }) => {
    await expect(page.locator('gpf-genes-block')).toBeVisible();
    await expect(page.locator('gpf-pheno-tool-measure')).toBeVisible();
    await expect(page.locator('gpf-pheno-tool-genotype-block')).toBeVisible();
    await expect(page.locator('gpf-family-filters-block')).toBeVisible();
    await expect(page.getByText('Report')).toBeVisible();
    await expect(page.locator('#save-query-dropdown-button')).toBeVisible();
    await expect(page.getByText('Download')).toBeVisible();
  });

  test('should display pheno tool results chart after "Report" button click', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();
    await expect(page.locator('gpf-pheno-tool-measure gpf-errors-alert .alert-danger')).toBeVisible();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await page.locator('gpf-pheno-tool').getByText('Report').click();
    await page.waitForSelector('gpf-pheno-tool-results-chart');
    await expect(page.locator('gpf-pheno-tool-results-chart')).toBeVisible();
  });

  test('should hide pheno tool results chart on state change', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();

    await page.getByPlaceholder('Select or start typing to search').click();
    await page.getByText('i1.age').first().click();
    await page.locator('gpf-pheno-tool').getByText('Report').click();
    await page.waitForSelector('gpf-pheno-tool-results-chart');
    await expect(page.locator('gpf-pheno-tool-results-chart')).toBeVisible();

    await page.locator('gpf-pheno-tool-effect-types button').getByText('None').click();

    await expect(page.locator('gpf-pheno-tool-results-chart')).not.toBeVisible();
  });

  test('should proplery disable the "Report", "Save/share query" and "Download" buttons on errors', async({
    page
  }) => {
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('#clear-measure-button').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('input#search-box').click();
    await page.getByText('i1.age').first().click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();
    await page.locator('gpf-present-in-parent button').filter({ hasText: 'None'}).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('gpf-present-in-parent button').filter({ hasText: 'All' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('gpf-pheno-tool-effect-types button').filter({ hasText: 'None' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();
    await page.locator('gpf-pheno-tool-effect-types button').filter({ hasText: 'All' }).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.locator('#family-ids').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.locator('gpf-family-ids textarea').fill('f1');
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();

    await page.getByText('Advanced').click();
    await expect(page.locator('#save-query-dropdown-button')).toBeDisabled();
    await expect(page.getByText('Report')).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();

    await page.getByLabel('Advanced').getByPlaceholder('Select or start typing to search').click();
    await page.locator('.dropdown-item span', {hasText: 'i1.age'}).click();
    await expect(page.locator('#save-query-dropdown-button')).toBeEnabled();
    await expect(page.getByText('Report')).toBeEnabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeEnabled();
  });
});

test.describe('Pheno tool download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Phenotype tool');
  });
  test('should download i1.m1 and check if it equals the reference data', async({ page }) => {
    await page.locator('input#search-box').click();
    await page.getByText('i1.m1').first().click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByText('Download').click();
    const download = await downloadPromise;
    const downloadData = scanCSV(await download.path(), {nullValues: '-'});
    const fixtureData = scanCSV('playwright/fixtures/pheno-tool/pheno_report1.csv', {nullValues: '-'});
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.frameEqual(downloadFrame));
  });

  [
    {id: '2', measure: 'i1.m2', normalizedBy: 'Age'},
    {id: '3', measure: 'i1.age', normalizedBy: 'Non verbal IQ'}
  ].forEach(data => {
    test(`should normalize by "
      ${data.normalizedBy}
    ", download report and compare it to the reference data`, async({ page }) => {
      await page.locator('input#search-box').click();
      await page.getByText(data.measure).first().click();
      await page.getByLabel(data.normalizedBy).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByText('Download').click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {id: '4', filters: ['father only', 'mother and father', 'Nonsense', 'Nonsynonymous', 'Synonymous'] },
    {id: '5', filters: ['mother only', 'mother and father', 'neither', 'LGDs', 'Splice-site', 'Frame-shift'] }
  ].forEach(data => {
    test(`should apply ${
      data.filters.toString()
    } filters, download report and compare it to the reference data`, async({ page }) => {
      await page.locator('input#search-box').click();
      await page.getByText('i1.m1').first().click();


      await page.locator('gpf-checkbox-list').getByRole('button', { name: 'None' }).click();
      await page.locator('gpf-pheno-tool-effect-types').getByRole('button', { name: 'None' }).click();

      for (const filter of data.filters) {
        await page.getByText(filter, {exact: true}).click();
      }

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByText('Download').click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {id: '6', familyId: 'f1'},
    {id: '7', familyId: 'f3'}
  ].forEach(data => {
    test(`should check downloaded report with family id ${data.familyId}`, async({ page }) => {
      await page.locator('input#search-box').click();
      await page.getByText('i1.age').first().click();

      await page.locator('#family-ids').click();
      await page.locator('gpf-family-ids textarea').fill(data.familyId);

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByText('Download').click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {id: '8', familyFilter: 'i1.iq', familyHistogramfromTo: ['33', '130']},
    {id: '9', familyFilter: 'i1.m1', familyHistogramfromTo: ['84', '107']}
  ].forEach(data => {
    test(`should test advanced family filters with ${data.familyFilter}`, async({ page }) => {
      await page.locator('input#search-box').click();
      await page.getByText('i1.age').first().click();

      await page.getByRole('tab', { name: 'Advanced' }).click();
      await page.getByLabel('Advanced').getByPlaceholder('Select or start typing to search').click();
      await page.locator('.dropdown-item span', {hasText: data.familyFilter}).click();

      await expect(page.locator('gpf-histogram')).toBeVisible();
      await page.locator('#from-input-field').clear();
      await page.locator('#from-input-field').fill(data.familyHistogramfromTo[0]);

      await page.waitForResponse(
        resp => resp.url().includes('/api/v3/measures/partitions') && resp.status() === 200
      );

      await page.locator('#to-input-field').clear();
      await page.locator('#to-input-field').fill(data.familyHistogramfromTo[1]);

      await page.waitForResponse(
        resp => resp.url().includes('/api/v3/measures/partitions') && resp.status() === 200
      );

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByText('Download').click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {id: '10', geneSymbol: 'CAMSAP1'},
    {id: '11', geneSymbol: 'SAMD11'}
  ].forEach(data => {
    test(`should check downloaded report with gene symbol ${data.geneSymbol}`, async({ page }) => {
      await page.locator('li#gene-symbols').click();
      await page.locator('gpf-gene-symbols textarea').fill(data.geneSymbol);

      await page.locator('input#search-box').click();
      await page.getByText('i1.age').click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByText('Download').click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {id: '12', collection: 'SFARI Genes', set: 'SFARI ALL (910): SFARI Genes (2017-09): All genes', measure: 'i1.age'},
    {id: '13', collection: 'Protein domains', set: 'AMOP (3)', measure: 'i1.iq'}
  ].forEach(data => {
    test(`should check downloaded report with gene sets collection ${data.collection}`, async({ page }) => {
      await page.getByRole('tab', { name: 'Gene Sets' }).click();

      await page.locator('gpf-gene-sets select.form-control').selectOption(data.collection);
      await page.getByLabel('Gene Sets').getByPlaceholder('Select or start typing to search').click();
      await page.getByLabel('Gene Sets')
        .getByPlaceholder('Select or start typing to search').focus();
      await page.keyboard.type(data.set.substring(0, data.set.indexOf(' (')));
      await page.getByRole('option', { name: data.set}).click();

      await page.locator('gpf-pheno-tool-measure #search-box').click();
      await page.getByText(data.measure).first().click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByRole('button', { name: 'Download' }).click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {
      id: '14',
      genotype: 'comp_vcf',
      affectedStatus: 'affected',
      set: 'Missense.Male (1): Missense.Male (comp_all:status:affected;comp_vcf:status:affected)',
      measure: 'i1.age'
    },
    {
      id: '15',
      genotype: 'iossifov_2014',
      affectedStatus: 'unaffected',
      set: 'LGDs.Recurrent (3): LGDs.Recurrent (comp_all:status:affected;iossifov_2014:status:unaffected)',
      measure: 'i1.iq'
    }
  ].forEach(data => {
    test(`should check downloaded report with gene set Denovo and measure${data.measure}`, async({ page }) => {
      await page.getByRole('tab', { name: 'Gene Sets' }).click();
      await page.locator('gpf-gene-sets select.form-control').selectOption('Denovo');

      await page.locator('ngb-accordion').filter({ hasText: data.genotype + ': Affected Status' }).click();
      await page.getByRole('button', { name: `${data.genotype}: Affected Status` }).click();
      await page.locator(`#${data.genotype}-checkbox-${data.affectedStatus}`).click();

      await page.getByLabel('Gene Sets').getByPlaceholder('Select or start typing to search').click();
      await page.getByRole('option', { name: data.set}).click();

      await page.locator('gpf-pheno-tool-measure #search-box').click();
      await page.locator('.dropdown-item span', {hasText: data.measure}).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByRole('button', { name: 'Download' }).click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });

  [
    {
      id: '16', measure: 'i1.age',
      geneScore: 'LGD rank - Gene rank after sorting by LGD vulnerability score',
      geneScoresHistogramFromTo: ['2944', '14716']
    },
    {
      id: '17',
      measure: 'i1.m1',
      geneScore: 'pRec - Probability of biallelic loss-of-function intolerance',
      geneScoresHistogramFromTo: ['0.000012', '0.832']
    }
  ].forEach(data => {
    test(`should check downloaded report with gene score ${data.geneScore}`, async({ page }) => {
      await page.getByRole('tab', { name: 'Gene Scores' }).click();
      await page.locator('#gene-scores-panel select.form-control').selectOption(data.geneScore);

      await page.locator('input#search-box').click();
      await page.getByText(data.measure).first().click();

      await page.locator('#from-input-field').clear();
      await page.locator('#from-input-field').fill(data.geneScoresHistogramFromTo[0]);
      await page.locator('#to-input-field').clear();
      await page.locator('#to-input-field').fill(data.geneScoresHistogramFromTo[1]);

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await page.getByRole('button', { name: 'Download' }).click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`playwright/fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.frameEqual(downloadFrame));
    });
  });
});
