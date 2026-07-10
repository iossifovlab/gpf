import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { EnrichmentToolPage } from './pages/enrichment-tool.page';

test.describe('Enrichment tool tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Enrichment tool');
  });

  test('should display enrichment tool elements', async({ page }) => {
    const enrichmentTool = new EnrichmentToolPage(page);
    await expect(enrichmentTool.genesBlock.root).toBeVisible();
    await expect(enrichmentTool.insertGeneSymbolError).toBeVisible();
    await page.waitForSelector('gpf-enrichment-models-block');
    await expect(enrichmentTool.modelsBlock).toBeVisible();
    await expect(enrichmentTool.enrichmentTestButton).toBeVisible();
    await expect(enrichmentTool.shareSaveQueryButton).toBeVisible();
  });

  test('should display enrichment table after "Enrichment Test" button click', async({ page }) => {
    const enrichmentTool = new EnrichmentToolPage(page);
    await expect(enrichmentTool.enrichmentTable).not.toBeVisible();
    await expect(enrichmentTool.insertGeneSymbolError).toBeVisible();

    await page.waitForSelector('#background-models');
    await page.waitForSelector('#counting-models');

    await enrichmentTool.genesBlock.geneSymbols.type('CAMSAP1');
    await expect(enrichmentTool.genesBlock.geneSymbols.errorsAlert).not.toBeVisible();

    await enrichmentTool.enrichmentTestButton.click();
    await expect(enrichmentTool.enrichmentTable).toBeVisible();
  });

  test('should display alert window when the gene sets textarea is empty', async({ page }) => {
    const enrichmentTool = new EnrichmentToolPage(page);
    const geneSets = enrichmentTool.genesBlock.geneSets;

    await enrichmentTool.genesBlock.openGeneSets();
    await page.waitForSelector('gpf-gene-sets');

    await geneSets.selectCollectionForm('Relevant Gene Sets');

    await expect(enrichmentTool.selectGeneSetError).toBeVisible();
    await enrichmentTool.searchBox.click();
    await enrichmentTool.searchBox.focus();
    await page.keyboard.type('synaptic clefts inhibitory');

    await geneSets.optionByTitle('synaptic clefts inhibitory (41): ' +
    'Ken H. Loh, et al. Proteomic Analysis of Unbounded Cellular Compartments: Synaptic Clefts. Cell (2016)').waitFor();

    await geneSets.optionByText('synaptic clefts inhibitory (41): Ken H. Loh, et al. ' +
    'Proteomic Analysis of Unbounded Cellular Compartments: Synaptic Clefts. Cell (2016)').click();

    await enrichmentTool.enrichmentTestButton.click();
    await expect(enrichmentTool.enrichmentTable).toBeVisible();
  });

  test('should check the affected person\'s observed column ' +
  'of LGDs and missense\'s rows respectively with gene set Main: FMRP Darnell', async({ page }) => {
    const enrichmentTool = new EnrichmentToolPage(page);
    const geneSets = enrichmentTool.genesBlock.geneSets;

    await enrichmentTool.genesBlock.openGeneSets();

    await geneSets.selectCollectionForm('Relevant Gene Sets');

    await page.waitForSelector('gpf-gene-sets');
    await enrichmentTool.searchBox.click();
    await enrichmentTool.searchBox.focus();
    await page.keyboard.type('FMRP Darnell');

    await geneSets.optionByTitle('FMRP Darnell (842): Darnell JC., et al. FMRP stalls ribosomal ' +
    'translocation on mRNAs linked to synaptic function and autism. Cell (2011)').waitFor();
    await geneSets.optionByText('FMRP Darnell (842): Darnell JC., et al. FMRP stalls ribosomal ' +
    'translocation on mRNAs linked to synaptic function and autism. Cell (2011)').click();

    await enrichmentTool.enrichmentTestButton.click();
    await page.waitForSelector('.enrichment-table');

    await expect(enrichmentTool.tableCell(3, 2)).toHaveText('10');
    await expect(enrichmentTool.tableCell(4, 2)).toHaveText('20');
    await expect(enrichmentTool.tableCell(3, 3)).toHaveText('5.40');
    await expect(enrichmentTool.tableCell(4, 3)).toHaveText('22.06');
  });

  test('should check the affected person\'s observed column ' +
  'of LGDs and missense\'s rows respectively with gene set MSigDB Pathways: BIOCARTA_PTEN_PATHWAY', async({ page }) => {
    const enrichmentTool = new EnrichmentToolPage(page);
    const geneSets = enrichmentTool.genesBlock.geneSets;

    await enrichmentTool.genesBlock.openGeneSets();
    await page.waitForSelector('gpf-gene-sets');

    await geneSets.selectCollectionForm('MSigDB Pathways');
    await enrichmentTool.searchBox.click();
    await enrichmentTool.searchBox.focus();
    await page.keyboard.type('BIOCARTA_PTEN_PATHWAY');

    await geneSets.optionByTitle('BIOCARTA_PTEN_PATHWAY (18): ' +
    'http://www.gsea-msigdb.org/gsea/msigdb/cards/BIOCARTA_PTEN_PATHWAY').waitFor();
    await geneSets.optionByText('BIOCARTA_PTEN_PATHWAY (18): ' +
    'http://www.gsea-msigdb.org/gsea/msigdb/cards/BIOCARTA_PTEN_PATHWAY').click();

    await enrichmentTool.enrichmentTestButton.click();
    await page.waitForSelector('.enrichment-table');

    await expect(enrichmentTool.tableCell(3, 2)).toHaveText('0');
    await expect(enrichmentTool.tableCell(4, 2)).toHaveText('0');
    await expect(enrichmentTool.tableCell(3, 3)).toHaveText('0.06');
    await expect(enrichmentTool.tableCell(4, 3)).toHaveText('0.24');
  });
});
