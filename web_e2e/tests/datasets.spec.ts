import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Dataset navigation tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Dataset Statistics');
  });

  test('should toggle studies dropdown menu', async({ page }) => {
    await expect(page.locator('#datasets-dropdown-menu-button')).toHaveAttribute('aria-expanded', 'false');
    await page.locator('#datasets-dropdown-menu-button').click();
    await expect(page.locator('#datasets-dropdown-menu-button')).toHaveAttribute('aria-expanded', 'true');
    await page.locator('#datasets-dropdown-menu-button').click();
    await expect(page.locator('#datasets-dropdown-menu-button')).toHaveAttribute('aria-expanded', 'false');
  });

  test('should display genotype browser', async({ page }) => {
    await expect(page.locator('gpf-genotype-browser')).not.toBeVisible();
    await page.getByText('Genotype browser').click();
    await expect(page.locator('gpf-genotype-browser')).toBeVisible();
  });

  test('should display phenotype browser', async({ page }) => {
    await expect(page.locator('gpf-pheno-browser')).not.toBeVisible();
    await page.getByText('Phenotype browser').click();
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
  });

  test('should display phenotype tool', async({ page }) => {
    await expect(page.locator('gpf-pheno-tool')).not.toBeVisible();
    await page.getByText('Phenotype tool').click();
    await expect(page.locator('gpf-pheno-tool')).toBeVisible();
  });

  test('should display dataset statistics', async({ page }) => {
    await expect(page.locator('gpf-variant-reports')).toBeVisible();
    await page.getByText('Genotype browser').click();
    await expect(page.locator('gpf-variant-reports')).not.toBeVisible();

    await page.getByText('Dataset Statistics').click();
    await expect(page.locator('gpf-variant-reports')).toBeVisible();
  });

  test('should change url correctly after clicking on a dataset from the dataset dropdown menu', async({ page }) => {
    const datasets = [
      {id: utils.datasetIds.allGenotypes, url: 'ALL_genotypes'},
      {id: utils.datasetIds.helloWorldGenotypes, url: 'helloworld_genotypes'},
      {id: utils.datasetIds.denovoHelloWorld, url: 'denovo_helloworld'},
      {id: utils.datasetIds.vcfHelloWorld, url: 'vcf_helloworld'},
      {id: utils.datasetIds.multiLiftover, url: 'multi_liftover'},
      {id: utils.datasetIds.iossifov2014Liftover, url: 'iossifov_2014_liftover'},
      {id: utils.datasetIds.phenoHelloWorld, url: 'pheno_helloworld'}
    ];

    for (const dataset of datasets) {
      // eslint-disable-next-line no-await-in-loop
      await page.locator('#datasets-dropdown-menu-button').click();
      // eslint-disable-next-line no-await-in-loop
      await page.locator('a').filter({ hasText: dataset.id }).click();
      expect(page.url()).toContain(utils.frontendUrl + '/datasets/' + dataset.url);
    }
  });

  test('navigation to invalid dataset', async({ page }) => {
    await page.goto(`${utils.frontendUrl}/datasets/iossifov_2014_liftover/gene-browser`);
    await expect(page.locator('gpf-gene-browser')).toBeVisible();
    await expect(page.locator('.alert-danger')).not.toBeVisible();

    await page.goto(`${utils.frontendUrl}/datasets/SFARI_SSC_WGS_CSHL/gene-browser`);
    await page.waitForSelector('.alert-danger');
    await expect(page.locator('.alert-danger')).toContainText('No such dataset found!');
    await expect(page.locator('gpf-gene-browser')).not.toBeVisible();
  });
});