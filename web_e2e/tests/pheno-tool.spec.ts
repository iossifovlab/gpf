import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { PhenoToolPage } from './pages/pheno-tool.page';

test.describe('Pheno tool tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Phenotype tool');
  });

  test('should display pheno tool elements', async({ page }) => {
    const phenoToolPage = new PhenoToolPage(page);
    await expect(phenoToolPage.genesBlock.root).toBeVisible();
    await expect(phenoToolPage.measure.root).toBeVisible();
    await expect(phenoToolPage.genotypeBlock).toBeVisible();
    await expect(phenoToolPage.familyFilters.root).toBeVisible();
    await expect(phenoToolPage.reportButton).toBeVisible();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeVisible();
    await expect(phenoToolPage.downloadButton).toBeVisible();
  });

  test('should display pheno tool results chart after "Report" button click', async({ page }) => {
    const phenoToolPage = new PhenoToolPage(page);
    await expect(phenoToolPage.resultsChart).not.toBeVisible();
    await expect(phenoToolPage.measureErrorAlert).toBeVisible();

    await phenoToolPage.measure.selectMeasure('instrument_1.age');
    await phenoToolPage.clickReport();
    await phenoToolPage.resultsChart.waitFor();
    await expect(phenoToolPage.resultsChart).toBeVisible();
  });

  test('should hide pheno tool results chart on state change', async({ page }) => {
    const phenoToolPage = new PhenoToolPage(page);
    await expect(phenoToolPage.resultsChart).not.toBeVisible();

    await page.getByPlaceholder('Select or start typing to search').click();
    await page.getByText('instrument_1.age').first().click();
    await phenoToolPage.clickReport();
    await phenoToolPage.resultsChart.waitFor();
    await expect(phenoToolPage.resultsChart).toBeVisible();

    await phenoToolPage.effectTypesButton('None').click();

    await expect(phenoToolPage.resultsChart).not.toBeVisible();
  });

  test('should proplery disable the "Report", "Save/share query" and "Download" buttons on errors', async({
    page
  }) => {
    const phenoToolPage = new PhenoToolPage(page);

    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();

    await phenoToolPage.measure.selectMeasure('instrument_1.age');
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();

    await phenoToolPage.measure.clearMeasureButton.click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();

    await phenoToolPage.measure.selectMeasure('instrument_1.age');
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();
    await phenoToolPage.presentInParent.button('None').click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();

    await phenoToolPage.presentInParent.button('All').click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();

    await phenoToolPage.effectTypesButton('None').click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();
    await phenoToolPage.effectTypesButton('All').click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();

    await phenoToolPage.familyIdsToggle.click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();

    await phenoToolPage.familyIds.textarea.pressSequentially('f1');
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();

    await phenoToolPage.tab('Advanced').click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeDisabled();
    await expect(phenoToolPage.reportButton).toBeDisabled();
    await expect(phenoToolPage.downloadButton).toBeDisabled();

    await page.getByLabel('Advanced').getByPlaceholder('Select or start typing to search').click();
    await phenoToolPage.dropdownItemSpans.filter({ hasText: 'instrument_1.age' }).click();
    await expect(phenoToolPage.saveQueryDropdownButton).toBeEnabled();
    await expect(phenoToolPage.reportButton).toBeEnabled();
    await expect(phenoToolPage.downloadButton).toBeEnabled();
  });

  test('should check present in parent default state when study doesn\'t have denovo', async({ page }) => {
    const phenoToolPage = new PhenoToolPage(page);

    await expect(phenoToolPage.presentInParent.checkbox('mother only')).not.toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('father only')).not.toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('mother and father')).not.toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('neither')).toBeChecked();
    await expect(phenoToolPage.presentInParent.ultraRareRadio()).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.vcfHelloWorld, 'Phenotype tool');
    await expect(phenoToolPage.presentInParent.checkbox('mother only')).toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('father only')).toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('mother and father')).toBeChecked();
    await expect(phenoToolPage.presentInParent.checkbox('neither')).toBeChecked();
    await expect(phenoToolPage.presentInParent.ultraRareRadio()).toBeChecked();
  });
});

test.describe('Pheno tool download tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.vcfHelloWorld, 'Phenotype tool');
  });
  test('should download instrument_1.measure_1 and check if it equals the reference data', async({ page }) => {
    const phenoToolPage = new PhenoToolPage(page);
    await phenoToolPage.measure.selectMeasure('instrument_1.measure_1');

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await phenoToolPage.downloadButton.click();
    const download = await downloadPromise;
    const downloadData = scanCSV(await download.path(), {nullValues: '-'});
    const fixtureData = scanCSV('fixtures/pheno-tool/pheno_report1.csv', {nullValues: '-'});
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  [
    {id: '2', measure: 'instrument_1.measure_2', normalizedBy: 'Age'},
    {id: '3', measure: 'instrument_1.age', normalizedBy: 'Non verbal IQ'}
  ].forEach(data => {
    test(`should normalize by "
      ${data.normalizedBy}
    ", download report and compare it to the reference data`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.measure.selectMeasure(data.measure);
      await phenoToolPage.measure.normalizationCheckbox(data.normalizedBy).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {id: '4', filters: ['father only', 'mother and father', 'Nonsense', 'Nonsynonymous', 'Synonymous'] },
    {id: '5', filters: ['mother only', 'mother and father', 'neither', 'LGDs', 'Splice-site', 'Frame-shift'] }
  ].forEach(data => {
    test(`should apply ${
      data.filters.toString()
    } filters, download report and compare it to the reference data`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.measure.selectMeasure('instrument_1.measure_1');


      await phenoToolPage.checkboxList.getByRole('button', { name: 'None' }).click();
      await phenoToolPage.effectTypesButton('None').click();

      for (const filter of data.filters) {
        // eslint-disable-next-line no-await-in-loop
        await page.getByText(filter, {exact: true}).click();
      }

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {id: '6', familyId: 'f1'},
    {id: '7', familyId: 'f2'}
  ].forEach(data => {
    test(`should check downloaded report with family id ${data.familyId}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.measure.selectMeasure('instrument_1.age');

      await phenoToolPage.familyIdsToggle.click();
      await phenoToolPage.familyIds.textarea.pressSequentially(data.familyId);

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {id: '8', familyFilter: 'instrument_1.iq', familyHistogramfromTo: ['33', '130']},
    {id: '9', familyFilter: 'instrument_1.measure_1', familyHistogramfromTo: ['50', '120']}
  ].forEach(data => {
    test(`should test advanced family filters with ${data.familyFilter}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.measure.selectMeasure('instrument_1.age');

      await phenoToolPage.tab('Advanced').click();
      await phenoToolPage.categoricalFilter.getByRole('button', { name: 'close' }).click();
      await page.getByLabel('Advanced').getByPlaceholder('Select or start typing to search').click();
      await phenoToolPage.dropdownItemSpans.filter({ hasText: data.familyFilter }).click();

      await expect(phenoToolPage.histogram).toBeVisible();
      await phenoToolPage.fromInput.clear();
      await phenoToolPage.fromInput.pressSequentially(data.familyHistogramfromTo[0]);

      await page.waitForResponse(
        resp => resp.url().includes('/api/v3/measures/partitions') && resp.status() === 200
      );

      await phenoToolPage.toInput.clear();
      await phenoToolPage.toInput.pressSequentially(data.familyHistogramfromTo[1]);

      await page.waitForResponse(
        resp => resp.url().includes('/api/v3/measures/partitions') && resp.status() === 200
      );

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {id: '10', geneSymbol: 'CAMSAP1'},
    {id: '11', geneSymbol: 'SAMD11'}
  ].forEach(data => {
    test(`should check downloaded report with gene symbol ${data.geneSymbol}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.genesBlock.geneSymbolsToggle.click();
      await phenoToolPage.genesBlock.geneSymbols.textbox.focus();
      await page.keyboard.type(data.geneSymbol);

      await phenoToolPage.measure.selectMeasure('instrument_1.age');

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {
      id: '12',
      collection: 'GO Terms',
      set: 'GO:0000015-phosphopyruvate_hydratase_complex (4): https://www.ebi.ac.uk/QuickGO/term/GO:0000015',
      measure: 'instrument_1.age'
    },
    {
      id: '13',
      collection: 'Protein domains',
      set: 'AMOP (3)',
      measure: 'instrument_1.iq'
    }
  ].forEach(data => {
    test(`should check downloaded report with gene sets collection ${data.collection}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.genesBlock.openGeneSetsTab();

      await phenoToolPage.genesBlock.geneSets.selectCollectionForm(data.collection);
      await page.getByLabel('Gene Sets').getByPlaceholder('Select or start typing to search').click();
      await page.getByLabel('Gene Sets')
        .getByPlaceholder('Select or start typing to search').focus();
      await page.keyboard.type(data.set.substring(0, data.set.indexOf(' (')));
      await phenoToolPage.genesBlock.geneSets.option(data.set).click();

      await phenoToolPage.measure.searchBox.click();
      await page.getByText(data.measure).first().click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {
      id: '14',
      genotype: 'denovo_helloworld',
      affectedStatus: 'affected',
      set: 'Missense (5): Missense (vcf_helloworld:status:affected;denovo_helloworld:status:affected)',
      measure: 'instrument_1.age'
    },
    {
      id: '15',
      genotype: 'iossifov_2014_liftover',
      affectedStatus: 'unaffected',
      set: 'LGDs.Recurrent (1): LGDs.Recurrent '+
        '(vcf_helloworld:status:affected;iossifov_2014_liftover:status:unaffected)',
      measure: 'instrument_1.iq'
    }
  ].forEach(data => {
    test(`should check downloaded report with gene set Denovo and measure ${data.measure}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.genesBlock.openGeneSetsTab();
      await phenoToolPage.genesBlock.geneSets.selectCollectionForm('Denovo');

      await phenoToolPage.selectStudiesModal.open();
      await expect(phenoToolPage.selectStudiesModal.content).toBeVisible();

      await phenoToolPage.selectStudiesModal.datasetNode(data.genotype).click();
      const affectedCheckbox = data.affectedStatus === 'affected'
        ? phenoToolPage.selectStudiesModal.affectedCheckbox(data.genotype)
        : phenoToolPage.selectStudiesModal.unaffectedCheckbox(data.genotype);
      await affectedCheckbox.click();
      await page.mouse.click(0, 0); // close modal

      await page.getByLabel('Gene Sets').getByPlaceholder('Select or start typing to search').click();
      await phenoToolPage.genesBlock.geneSets.option(data.set).click();

      await phenoToolPage.measure.searchBox.click();
      await phenoToolPage.dropdownItemSpans.filter({ hasText: data.measure }).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });

  [
    {
      id: '16', measure: 'instrument_1.age',
      geneScore: 'LGD_rank - Gene rank after sorting by LGD vulnerability score',
      geneScoresHistogramFromTo: ['2944', '14716']
    },
    {
      id: '17',
      measure: 'instrument_1.measure_1',
      geneScore: 'pRec - Probability of biallelic loss-of-function intolerance',
      geneScoresHistogramFromTo: ['0.000012', '0.832']
    }
  ].forEach(data => {
    test(`should check downloaded report with gene score ${data.geneScore}`, async({ page }) => {
      const phenoToolPage = new PhenoToolPage(page);
      await phenoToolPage.genesBlock.openGeneScoresTab();
      await phenoToolPage.geneScoresPanelSelect.selectOption(data.geneScore);

      await phenoToolPage.measure.selectMeasure(data.measure);

      await phenoToolPage.fromInput.clear();
      await phenoToolPage.fromInput.pressSequentially(data.geneScoresHistogramFromTo[0]);
      await phenoToolPage.toInput.clear();
      await phenoToolPage.toInput.pressSequentially(data.geneScoresHistogramFromTo[1]);

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await phenoToolPage.downloadButton.click();
      const download = await downloadPromise;
      const downloadData = scanCSV(await download.path(), {nullValues: '-'});
      const fixtureData = scanCSV(`fixtures/pheno-tool/pheno_report${data.id}.csv`, {nullValues: '-'});
      const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
      const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });
});
