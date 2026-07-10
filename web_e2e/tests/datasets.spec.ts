import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { Datasets } from './components/datasets.component';

test.describe('Dataset navigation tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Dataset Statistics');
  });

  test('should toggle studies dropdown menu', async({ page }) => {
    const datasets = new Datasets(page);
    await expect(datasets.dropdownButton).toHaveAttribute('aria-expanded', 'false');
    await datasets.dropdownButton.click();
    await expect(datasets.dropdownButton).toHaveAttribute('aria-expanded', 'true');
    await datasets.dropdownButton.click();
    await expect(datasets.dropdownButton).toHaveAttribute('aria-expanded', 'false');
  });

  test('should display genotype browser', async({ page }) => {
    const datasets = new Datasets(page);
    await expect(datasets.genotypeBrowser).not.toBeVisible();
    await datasets.toolLink('Genotype browser').click();
    await expect(datasets.genotypeBrowser).toBeVisible();
  });

  test('should display phenotype browser', async({ page }) => {
    const datasets = new Datasets(page);
    await expect(datasets.phenoBrowser).not.toBeVisible();
    await datasets.toolLink('Phenotype browser').click();
    await expect(datasets.phenoBrowser).toBeVisible();
  });

  test('should display phenotype tool', async({ page }) => {
    const datasets = new Datasets(page);
    await expect(datasets.phenoTool).not.toBeVisible();
    await datasets.toolLink('Phenotype tool').click();
    await expect(datasets.phenoTool).toBeVisible();
  });

  test('should display dataset statistics', async({ page }) => {
    const datasets = new Datasets(page);
    await expect(datasets.variantReports).toBeVisible();
    await datasets.toolLink('Genotype browser').click();
    await expect(datasets.variantReports).not.toBeVisible();

    await datasets.toolLink('Dataset Statistics').click();
    await expect(datasets.variantReports).toBeVisible();
  });

  test('should change url correctly after clicking on a dataset from the dataset dropdown menu', async({ page }) => {
    const datasets = new Datasets(page);
    const datasetsList = [
      {id: utils.datasetIds.allGenotypes, url: 'ALL_genotypes'},
      {id: utils.datasetIds.helloWorldGenotypes, url: 'helloworld_genotypes'},
      {id: utils.datasetIds.denovoHelloWorld, url: 'denovo_helloworld'},
      {id: utils.datasetIds.vcfHelloWorld, url: 'vcf_helloworld'},
      {id: utils.datasetIds.multiLiftover, url: 'multi_liftover'},
      {id: utils.datasetIds.iossifov2014Liftover, url: 'iossifov_2014_liftover'},
      {id: utils.datasetIds.phenoHelloWorld, url: 'pheno_helloworld'}
    ];

    for (const dataset of datasetsList) {
      // eslint-disable-next-line no-await-in-loop
      await datasets.dropdownButton.click();
      // eslint-disable-next-line no-await-in-loop
      await datasets.dropdownLink(dataset.id).click();
      expect(page.url()).toContain(utils.frontendUrl + '/datasets/' + dataset.url);
    }
  });

  test('navigation to invalid dataset', async({ page }) => {
    const datasets = new Datasets(page);
    await page.goto(`${utils.frontendUrl}/datasets/iossifov_2014_liftover/gene-browser`);
    await expect(datasets.geneBrowser).toBeVisible();
    await expect(datasets.alertDanger).not.toBeVisible();

    await page.goto(`${utils.frontendUrl}/datasets/SFARI_SSC_WGS_CSHL/gene-browser`);
    await page.waitForSelector('.alert-danger');
    await expect(datasets.alertDanger).toContainText('No such dataset found!');
    await expect(datasets.geneBrowser).not.toBeVisible();
  });
});

test.describe('Access rights and icons', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
  });
  test('list of icons of different datasets in datasets dropdown', async({ page }) => {
    const datasets = new Datasets(page);
    await utils.openDatasetDropdown(page);
    await utils.expandDataset(page, utils.datasetIds.helloWorldGenotypes);

    // denovo_helloworld
    await expect(
      datasets.datasetNode(utils.datasetIds.denovoHelloWorld)
    ).toHaveText('denovo_helloworldgeneticskid_starhow_to_reg');

    // vcf_helloworld
    await expect(
      datasets.datasetNode(utils.datasetIds.vcfHelloWorld)
    ).toHaveText('vcf_helloworldfamily_historyhow_to_reg');

    // iossifov_2014_liftover
    await expect(
      datasets.datasetNode(utils.datasetIds.iossifov2014Liftover)
    ).toHaveText('iossifov_2014_liftovergeneticskid_star');

    // pheno_helloworld
    await expect(
      datasets.datasetNode(utils.datasetIds.phenoHelloWorld)
    ).toHaveText('pheno_helloworldhow_to_reg');

    // All Genotypes
    await expect(
      datasets.datasetNode(utils.datasetIds.allGenotypes)
    ).toHaveText('ALL Genotypesgeneticskid_starfamily_history');
  });

  test('list of icons of selected dataset', async({ page }) => {
    const datasets = new Datasets(page);
    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(
      datasets.dropdownButton
    ).toHaveText('denovo_helloworldgeneticskid_starhow_to_reg');
  });

  test('colors of icons of Hello World Genotypes when user has no access rights', async({ page }) => {
    const datasets = new Datasets(page);
    await utils.logout(page);
    await utils.openDatasetDropdown(page);

    const helloWorldGenotypes = datasets.datasetNode(utils.datasetIds.helloWorldGenotypes);
    await expect(helloWorldGenotypes).toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypes.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(helloWorldGenotypes.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');

    await utils.loginWorkerUser(page);
    await utils.openDatasetDropdown(page);

    await expect(helloWorldGenotypes).toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypes.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  test('colors of icons of selected dataset when user has no access rights', async({ page }) => {
    const datasets = new Datasets(page);
    await utils.logout(page);
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(
      datasets.dropdownButtonIcon('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(
      datasets.dropdownButtonIcon('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');

    await utils.loginWorkerUser(page);
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(
      datasets.dropdownButtonIcon('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(
      datasets.dropdownButtonIcon('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  // tb-nxl-fix: the four admin Management-write tests that used to live
  // here ("should give rights for vcf_helloworld to {any_user,researcher}",
  // same for pheno_helloworld) moved to user-management.spec.ts. They
  // need admin and serial coexistence with other Management writes; the
  // file-level serial worker that owns user-management.spec.ts is the
  // only place those guarantees hold under workers=16 fullyParallel.
});
