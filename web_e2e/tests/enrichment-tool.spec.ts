import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Enrichment tool tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Enrichment tool');
  });

  test('should display enrichment tool elements', async({ page }) => {
    await expect(page.locator('gpf-genes-block')).toBeVisible();
    await expect(page.getByText('Please insert at least one gene symbol.')).toBeVisible();
    await page.waitForSelector('gpf-enrichment-models-block');
    await expect(page.locator('gpf-enrichment-models-block')).toBeVisible();
    await expect(page.getByRole('button', {name: 'Enrichment test'})).toBeVisible();
    await expect(page.getByRole('button', {name: 'Share/save query'})).toBeVisible();
  });

  test('should display enrichment table after "Enrichment Test" button click', async({ page }) => {
    await expect(page.locator('.enrichment-table')).not.toBeVisible();

    await page.locator('gpf-gene-symbols textarea').fill('CAMSAP1');

    await page.getByRole('button', {name: 'Enrichment test'}).click();
    await expect(page.locator('.enrichment-table')).toBeVisible();
  });

  test('should display alert window when the gene sets textarea is empty', async({ page }) => {
    await page.locator('#gene-sets').click();
    await page.waitForSelector('gpf-gene-sets');
    await expect(page.getByText('Please select a gene set.')).toBeVisible();
    await page.locator('#search-box').click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('synaptic clefts inhibitory');

    await page.waitForSelector('[title="synaptic clefts inhibitory (41): ' +
    'Ken H. Loh, et al. Proteomic Analysis of Unbounded Cellular Compartments: Synaptic Clefts. Cell (2016)"]');

    await page.getByText('synaptic clefts inhibitory (41): Ken H. Loh, et al. ' +
    'Proteomic Analysis of Unbounded Cellular Compartments: Synaptic Clefts. Cell (2016)').click();

    await page.getByRole('button', {name: 'Enrichment test'}).click();
    await expect(page.locator('.enrichment-table')).toBeVisible();
  });

  test('should display "55" and "169" in the affected person\'s observed column ' +
  'of LGDs and missense\'s rows respectively with gene set Main: FMRP Darnell', async({ page }) => {
    await page.locator('#gene-sets').click();
    await page.waitForSelector('gpf-gene-sets');
    await page.locator('#search-box').click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('FMRP Darnell');

    await page.waitForSelector('[title="FMRP Darnell (842): Darnell JC., et al. FMRP stalls ribosomal ' +
    'translocation on mRNAs linked to synaptic function and autism. Cell (2011)"]');
    await page.getByText('FMRP Darnell (842): Darnell JC., et al. FMRP stalls ribosomal ' +
    'translocation on mRNAs linked to synaptic function and autism. Cell (2011)').click();

    await page.getByRole('button', {name: 'Enrichment test'}).click();
    await page.waitForSelector('.enrichment-table');

    await expect(page.locator('.enrichment-table tr').nth(3).locator('td').nth(2)).toHaveText('55');
    await expect(page.locator('.enrichment-table tr').nth(4).locator('td').nth(2)).toHaveText('169');
    await expect(page.locator('.enrichment-table tr').nth(3).locator('td').nth(3)).toHaveText('35.01');
    await expect(page.locator('.enrichment-table tr').nth(4).locator('td').nth(3)).toHaveText('145.62');
  });

  test('should display "0" and "2" in the affected person"s observed column of LGDs and missense"s rows respectively ' +
  'with gene set MSigDB Pathways: BIOCARTA_PTEN_PATHWAY', async({ page }) => {
    await page.locator('#gene-sets').click();
    await page.waitForSelector('gpf-gene-sets');

    await page.locator('gpf-gene-sets select').selectOption('MSigDB Pathways');
    await page.locator('#search-box').click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('BIOCARTA_PTEN_PATHWAY');

    await page.waitForSelector('[title="BIOCARTA_PTEN_PATHWAY (18): ' +
    'http://www.broadinstitute.org/gsea/msigdb/cards/BIOCARTA_PTEN_PATHWAY"]');
    await page.getByText('BIOCARTA_PTEN_PATHWAY (18): ' +
    'http://www.broadinstitute.org/gsea/msigdb/cards/BIOCARTA_PTEN_PATHWAY').click();

    await page.getByRole('button', {name: 'Enrichment test'}).click();
    await page.waitForSelector('.enrichment-table');

    await expect(page.locator('.enrichment-table tr').nth(3).locator('td').nth(2)).toHaveText('0');
    await expect(page.locator('.enrichment-table tr').nth(4).locator('td').nth(2)).toHaveText('2');
    await expect(page.locator('.enrichment-table tr').nth(3).locator('td').nth(3)).toHaveText('0.36');
    await expect(page.locator('.enrichment-table tr').nth(4).locator('td').nth(3)).toHaveText('1.52');
  });

  // add screenshot test for the table
});