/* eslint-disable indent */
import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { GenotypeBrowserPage } from './pages/genotype-browser.page';

test.describe('Genes block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display gene symbols panel', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneSymbolsPanel).toBeHidden();

    await genotypeBrowser.genes.openGeneSymbols();
    await expect(genotypeBrowser.genes.geneSymbolsPanel).toBeVisible();
  });

  test('should display gene sets panel', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneSetsPanelWrapper).toBeHidden();
    await genotypeBrowser.genes.openGeneSetsTab();
    await expect(genotypeBrowser.genes.geneSetsPanel).toBeVisible();
  });

  test('should display error alert in gene sets panel when the textarea is empty', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneSets = genotypeBrowser.genes.geneSets;
    await genotypeBrowser.genes.openGeneSetsTab();
    await expect(geneSets.alertDanger).toBeVisible();

    await geneSets.searchBox.click();

    await geneSets.firstMatOption.click();
    await expect(geneSets.alertDanger).not.toBeVisible();
  });

  test('should display error alert in gene sets panel when the textarea is cleared', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const geneSets = genotypeBrowser.genes.geneSets;
    await genotypeBrowser.genes.openGeneSetsTab();
    await geneSets.searchBox.click();

    await geneSets.firstMatOption.click();

    await geneSets.selectedValue.click();
    await expect(geneSets.alertDanger).toBeVisible();
  });

  test('should display gene weights panel', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneScoresPanel).toBeHidden();

    await genotypeBrowser.genes.openGeneScoresTab();
    await expect(genotypeBrowser.genes.geneScoresPanel).toBeVisible();
  });
});

test.describe('Genes sybmols tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneSymbolsTab();
  });

  test('should display error alert in gene symbols panel when the textarea is empty', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();

    await genotypeBrowser.genes.geneSymbols.textbox.focus();
    await page.keyboard.type('SAMD11');
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).not.toBeVisible();

    await genotypeBrowser.genes.geneSymbols.clear();
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();
  });

  test('error message display when textarea contains invalid gene', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();

    await genotypeBrowser.genes.geneSymbols.type(', DIABLO, CHD*');
    await expect(genotypeBrowser.genes.geneSymbols.invalidGenes('CHD*')).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('gene symbols state resetting when switching tabs', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('DIABLO\nSHANK2');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();

    await genotypeBrowser.switchToTool('Phenotype browser');
    await genotypeBrowser.switchToTool('Genotype browser');
    await genotypeBrowser.genes.openGeneSymbolsTab();

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toBeEmpty();
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('gene symbols state resetting when switching tools', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('DIABLO\nSHANK2');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    await genotypeBrowser.switchToTool('Phenotype browser');
    await genotypeBrowser.switchToTool('Genotype browser');
    await genotypeBrowser.genes.openGeneSymbolsTab();

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toBeEmpty();
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('gene symbols errors resetting when switching tabs', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('CHD*');
    await expect(genotypeBrowser.genes.geneSymbols.invalidGenes('CHD*')).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.genes.openAllTab();
    await genotypeBrowser.genes.openGeneSymbolsTab();

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toBeEmpty();
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('gene symbols errors resetting when switching tools', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('333');
    await expect(genotypeBrowser.genes.geneSymbols.invalidGenes('333')).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.switchToTool('Phenotype browser');
    await genotypeBrowser.switchToTool('Genotype browser');
    await genotypeBrowser.genes.openGeneSymbolsTab();

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toBeEmpty();
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('if gene symbols are loaded correctly when loading query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('DIABLO\nSHANK2, CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toContainText('DIABLO, SHANK2, CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('if gene symbols are formatted correctly when loading query with two genes', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('DIABLO\nSHANK2');

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toContainText('DIABLO\nSHANK2');
  });

  test('loaded variants when there are duplicate gene symbols', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('POGZ');
    await genotypeBrowser.effectTypes.clickButton('All');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('16 variants selected');

    await genotypeBrowser.genes.geneSymbols.type('\nPOGZ\nPOGZ');
    await expect(genotypeBrowser.previewTable).not.toBeVisible();
    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('16 variants selected');
  });

  test('case sensitivity of gene symbols', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.genes.geneSymbols.caseSensitiveNote).toBeVisible();
    await genotypeBrowser.genes.geneSymbols.type('CHD8');
    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('6 variants selected');

    await genotypeBrowser.genes.geneSymbols.clear();
    await genotypeBrowser.genes.geneSymbols.type('chd8');
    await expect(genotypeBrowser.genes.geneSymbols.invalidGenes('chd8')).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
  });

  test('if gene symbols input is trimmed when loading query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.geneSymbols.type('  ');
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toHaveCount(1);

    await genotypeBrowser.genes.geneSymbols.type('\n');
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toHaveCount(1);

    await genotypeBrowser.genes.geneSymbols.type('CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.emptyHint).toHaveCount(0);

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('6 variants selected');

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genotypeBrowser.genes.geneSymbols.textbox).toContainText('CHD8');
    await expect(genotypeBrowser.genes.geneSymbols.errorsAlert).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();

    await expect(async() => {
      await genotypeBrowser.runTablePreview();
      await expect(genotypeBrowser.previewTable).toBeVisible({timeout: 5000});
    }).toPass({intervals: [1000, 2000, 3000]});

    await expect(genotypeBrowser.variantsCount).toHaveText('6 variants selected', { timeout: 180000 });
  });
});

test.describe('Genes sets tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  [
    {
      collection: 'Protein domains',
      expectedSearchCondition: '7tm_1 (286): 7 transmembrane receptor (rhodopsin family)',
      expectedDownloadCount: '286'
    },
    {
      collection: 'GO Terms',
      expectedSearchCondition: 'GO:0000015-phosphopyruvate_hydratase_complex (4): https://www.ebi.ac.uk/QuickGO/term/GO:0000015',
      expectedDownloadCount: '4'
    },

  ].forEach(data => {
    test('should properly display "' + data.expectedSearchCondition + '" in "' +
      data.collection + '" collection, and the counts should match', async({ page }) => {
        const genotypeBrowser = new GenotypeBrowserPage(page);
        await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Genotype browser');
        await genotypeBrowser.genes.openGeneSetsTab();
        const geneSetsRequest = page.waitForRequest(utils.backendUrl + '/api/v3/gene_sets/gene_sets');
        await genotypeBrowser.genes.geneSets.selectCollection(data.collection);
        await geneSetsRequest;
        await genotypeBrowser.genes.geneSets.searchInput.click();

        const expectedSetName = data.expectedSearchCondition;
        const geneSetName = expectedSetName.substring(0, expectedSetName.indexOf('(') - 1);

        await genotypeBrowser.genes.geneSets.searchInput.pressSequentially(geneSetName);
        await page.waitForResponse(
            resp => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
        );
        await page.waitForLoadState('load');

        await genotypeBrowser.genes.geneSets.setsDropdownOptions.first().click();

        await expect(genotypeBrowser.genes.geneSets.selectedValue).toContainText(expectedSetName);

        const actualCountElement = await genotypeBrowser.genes.geneSets.countSpan.textContent();
        const actualCount = actualCountElement?.replace('Count: ', '').replace(' (Download)', '').trim();
        const expectedCount = data.expectedDownloadCount;
        expect(actualCount).toEqual(expectedCount);
        });
    });

  test('should select gene set, share query then check the state of gene set', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneSetsTab();
    await Promise.all([
      page.waitForRequest(utils.backendUrl + '/api/v3/gene_sets/gene_sets'),
      genotypeBrowser.genes.geneSets.selectCollection('GO Terms'),
    ]);

    await genotypeBrowser.genes.geneSets.searchInput.pressSequentially('GO:0000014');

    await genotypeBrowser.genes.geneSets.setsDropdownOption(
      'GO:0000014-single-stranded_DNA_endodeoxyribonuclease_activity (11): ' +
      'https://www.ebi.ac.uk/QuickGO/term/GO:0000014'
    ).click();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genotypeBrowser.genes.geneSets.selectedValue).toContainText(
      'GO:0000014-single-stranded_DNA_endodeoxyribonuclease_activity (11): ' +
      'https://www.ebi.ac.uk/QuickGO/term/GO:0000014'
    );
    await expect(genotypeBrowser.genes.geneSets.pleaseSelectHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
  });

  test('should reset invalid gene sets state when switching to All tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneSetsTab();
    await expect(genotypeBrowser.genes.geneSets.pleaseSelectHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.genes.openAllTab();
    await expect(genotypeBrowser.genes.geneSets.pleaseSelectHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should reset invalid gene sets state when switching to other tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.genes.openGeneSetsTab();
    await expect(genotypeBrowser.genes.geneSets.pleaseSelectHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.openToolLink('Gene Browser');
    await genotypeBrowser.openToolLink('Genotype Browser');

    await expect(genotypeBrowser.genes.geneSets.pleaseSelectHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });
});


test.describe('Gene block download tests ', () => {
test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
});

[
    {
      id: 1,
      collection: 'Relevant Gene Sets',
      searchValue: 'synaptic clefts inhibitory',
      geneSet: 'synaptic clefts inhibitory (41): Ken H. Loh, et al. '+
      'Proteomic Analysis of Unbounded Cellular Compartments: Synaptic Clefts. Cell (2016)',
      numOfRows: 42
    },
    {
      id: 2,
      searchValue: 'ABC1',
      collection: 'Protein domains',
      geneSet: 'ABC1 (5): ABC1 atypical kinase-like domain',
      numOfRows: 6
    },
    {
      id: 3,
      searchValue: 'GO:0000019',
      collection: 'GO Terms',
      geneSet: 'GO:0000019-regulation_of_mitotic_recombination (7): https://www.ebi.ac.uk/QuickGO/term/GO:0000019',
      numOfRows: 5
    }
].forEach(data => {
     test('should download "' + data.geneSet + '" in the "' + data.collection +
     '" collection and check whether the count in the name should matches ' +
     'the downloaded"s file length and the gene set"s name matches the first value of the file', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype Browser');

    await genotypeBrowser.genes.openGeneSets();
    await genotypeBrowser.genes.geneSets.selectCollectionForm(data.collection);


    await genotypeBrowser.genes.geneSets.selectCollectionForm(data.collection);
    await genotypeBrowser.genes.geneSets.searchInput.click();
    await genotypeBrowser.genes.geneSets.searchInput.focus();
    await page.keyboard.type(data.searchValue);
    await page.waitForResponse(
      resp => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
  );

      await expect(genotypeBrowser.genes.geneSets.option(data.geneSet)).toBeVisible();
      await genotypeBrowser.genes.geneSets.option(data.geneSet).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await genotypeBrowser.genes.geneSets.downloadLink.click();
      const download = await downloadPromise;

      const fixtureData = scanCSV(`fixtures/gene-sets/gene_sets${data.id}.csv`, {truncateRaggedLines: true});
      const downloadData = scanCSV(await download.path(), {truncateRaggedLines: true});
      const fixtureFrame = (await fixtureData.collect()).sort(fixtureData.columns[0]);
      const downloadFrame = (await downloadData.collect()).sort(downloadData.columns[0]);
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
    });
  });
});

test.describe('Denovo gene set tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, { waitUntil: 'load' });
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Genotype browser');
  });

  test('basic functionality', async({ page }) => {
      const genotypeBrowser = new GenotypeBrowserPage(page);
      const modal = genotypeBrowser.genes.geneSets.selectStudiesModal;
      await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Genotype browser');
      await genotypeBrowser.genes.openGeneSets();
      await expect(genotypeBrowser.genes.geneSetsPanel).toBeVisible();
      await genotypeBrowser.genes.geneSets.selectCollectionForm({ label: 'Denovo' });

      await modal.open();
      await expect(modal.content).toBeVisible();
      await expect(modal.hierarchy).toBeVisible();
      await expect(modal.filters).toBeVisible();
      await expect(modal.modalFilterList).toBeVisible();
      await expect(modal.datasetNode('denovo_helloworld')).not.toBeVisible();
      await expect(modal.datasetNode('vcf_helloworld')).not.toBeVisible();

      await modal.expandToggle('helloworld_genotypes').click();
      await expect(modal.datasetNode('denovo_helloworld')).toBeVisible();
      await expect(modal.datasetNode('vcf_helloworld')).toBeVisible();

      await expect(modal.datasetNode('helloworld_genotypes')).toHaveCSS('opacity', '0.3');
      await expect(modal.datasetNode('helloworld_genotypes')).toHaveCSS('pointer-events', 'none');

      await modal.datasetNode('denovo_helloworld').click();
      await expect(modal.datasetNode('iossifov_2014_liftover')).toHaveClass('btn-sm text-wrap modified');
      await expect(modal.affectedStatusLabel).toBeVisible();

      await modal.affectedCheckbox('denovo_helloworld').click();
      await modal.unaffectedCheckbox('denovo_helloworld').click();

      await expect(
        modal.modalFilterItem('iossifov_2014_liftover: status: affected')
      ).toBeVisible();

      await expect(
        modal.modalFilterItem('denovo_helloworld: status: affected')
      ).toBeVisible();

      await expect(
        modal.modalFilterItem('denovo_helloworld: status: unaffected')
      ).toBeVisible();
      await page.mouse.click(0, 0); // close modal

      await expect(modal.selectedFilterList).toBeVisible();
      await expect(modal.selectedFilterList).toContainText('iossifov_2014_liftover: status: affected');
      await expect(modal.selectedFilterList).toContainText('denovo_helloworld: status: affected');
      await expect(modal.selectedFilterList).toContainText('denovo_helloworld: status: unaffected');


      await modal.removeFilterButton('iossifov_2014_liftover: status: affected').click();
      await modal.removeFilterButton('denovo_helloworld: status: affected').click();

      await expect(modal.selectedFilterList).not.toContainText('iossifov_2014_liftover: status: affected');
      await expect(modal.selectedFilterList).not.toContainText('denovo_helloworld: status: affected');
      await expect(modal.selectedFilterList).toContainText('denovo_helloworld: status: unaffected');

      await modal.open();

      await expect(modal.affectedCheckbox('denovo_helloworld')).not.toBeChecked();
      await expect(modal.unaffectedCheckbox('denovo_helloworld')).toBeChecked();
      await expect(modal.datasetNode('iossifov_2014_liftover')).toHaveClass('btn-sm text-wrap');
      await expect(
        modal.modalFilterItem('iossifov_2014_liftover: status: affected')
      ).not.toBeVisible();

      await expect(
        modal.modalFilterItem('denovo_helloworld: status: affected')
      ).not.toBeVisible();

      await expect(
        modal.modalFilterItem('denovo_helloworld: status: unaffected')
      ).toBeVisible();
  });
  test('should download denovo_helloworld with affected status', async({ page }) => {
        const genotypeBrowser = new GenotypeBrowserPage(page);
        await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
        await genotypeBrowser.genes.openGeneSets();
        await expect(genotypeBrowser.genes.geneSetsPanel).toBeVisible();
        await genotypeBrowser.genes.geneSets.selectCollectionForm({ label: 'Denovo' });

        await genotypeBrowser.genes.geneSets.searchInput.click();
        await genotypeBrowser.genes.geneSets.searchInput.focus();
        await page.keyboard.type('Missense');
        await page.waitForResponse(
          (resp) => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
        );

      const geneSet = 'Missense (5): Missense (denovo_helloworld:status:affected)';
      await expect(genotypeBrowser.genes.geneSets.option(geneSet)).toBeVisible();
      await genotypeBrowser.genes.geneSets.option(geneSet).click();

      const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
      await genotypeBrowser.genes.geneSets.downloadLink.click();
      const download = await downloadPromise;

      const fixtureData = scanCSV('fixtures/gene-sets/gene_sets4.csv', {truncateRaggedLines: true});
      const downloadData = scanCSV(await download.path(), {truncateRaggedLines: true});
      const fixtureFrame = (await fixtureData.collect()).sort(fixtureData.columns[0]);
      const downloadFrame = (await downloadData.collect()).sort(downloadData.columns[0]);
      expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
      expect(downloadFrame.height).toBe(6);
    }
  );
});
