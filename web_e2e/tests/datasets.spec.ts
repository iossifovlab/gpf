import { test, expect, Page } from '@playwright/test';
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

test.describe('Access rights and icons', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });
  test('list of icons of different datasets in datasets dropdown', async({ page }) => {
    await utils.openDatasetDropdown(page);
    await utils.expandDataset(page, utils.datasetIds.helloWorldGenotypes);

    // denovo_helloworld
    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.denovoHelloWorld })
    ).toHaveText('denovo_helloworldgeneticskid_starhow_to_reg');

    // vcf_helloworld
    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.vcfHelloWorld })
    ).toHaveText('vcf_helloworldfamily_historyhow_to_reg');

    // iossifov_2014_liftover
    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.iossifov2014Liftover })
    ).toHaveText('iossifov_2014_liftovergeneticskid_star');

    // pheno_helloworld
    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.phenoHelloWorld })
    ).toHaveText('pheno_helloworldhow_to_reg');

    // All Genotypes
    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.allGenotypes })
    ).toHaveText('ALL Genotypesgeneticskid_starfamily_history');
  });

  test('list of icons of selected dataset', async({ page }) => {
    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(
      page.locator('#datasets-dropdown-menu-button')
    ).toHaveText('denovo_helloworldgeneticskid_starhow_to_reg');
  });

  test('colors of icons of Hello World Genotypes when user has no access rights', async({ page }) => {
    await utils.logout(page);
    await utils.openDatasetDropdown(page);

    const helloWorldGenotypes = page.locator('gpf-dataset-node a')
      .filter({ hasText: utils.datasetIds.helloWorldGenotypes });
    await expect(helloWorldGenotypes).toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypes.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(helloWorldGenotypes.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');

    await utils.loginAdmin(page);
    await utils.openDatasetDropdown(page);

    await expect(helloWorldGenotypes).toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypes.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypes.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  test('colors of icons of selected dataset when user has no access rights', async({ page }) => {
    await utils.logout(page);
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(
      page.locator('#datasets-dropdown-menu-button').locator('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(
      page.locator('#datasets-dropdown-menu-button').locator('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');

    await utils.loginAdmin(page);
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(
      page.locator('#datasets-dropdown-menu-button').locator('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(
      page.locator('#datasets-dropdown-menu-button').locator('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  test('should give rights for vcf_helloworld to any_user', async({ page }) => {
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);
    const study = utils.datasetIds.vcfHelloWorld;
    const group = 'any_user';
    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');

    // add any_user group to study
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);

    await page.locator(`[id="${study}-groups-cell"]`).getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await page.getByRole('button', { name: group }).click();

    await expect(page.locator(`[id="${study}-groups-cell"]`)).toContainText(group);

    // check if Genotype browser is enabled when no user is logged in
    await utils.logout(page);

    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    // remove any_user from list of groups of the study
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);
    await page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${group}-datasets-cell"] [id="${study}-list-item"]`)).not.toBeVisible();
  });

  test('should give rights for vcf_helloworld to researcher', async({ page }) => {
    // check if Genotype browser is disabled when no user is logged in
    await utils.logout(page);

    const study = utils.datasetIds.vcfHelloWorld;
    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');

    // add group to reasearcher
    const researcher = 'research@iossifovlab.com';
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"]`).getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await page.getByRole('button', { name: study }).click();

    await utils.logout(page);
    // check if Genotype browser is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.locator('li').filter({ hasText: 'Genotype Browser'})).toHaveClass('nav-item');

    // remove group from groups list of research
    await utils.logout(page);
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"] [id="${study}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${researcher}-groups-cell"]`)).not.toContainText(study);
  });

  test('should give rights for pheno_helloworld to any_user', async({ page }) => {
    const study = utils.datasetIds.phenoHelloWorld;
    const group = 'any_user';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).toContainClass('disabled-download');

    // add any_user group to pheno study
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);

    await page.locator(`[id="${study}-groups-cell"]`).getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, group);
    await page.waitForSelector(`button:text("${group}")`);
    await page.getByRole('button', { name: group }).click();

    await expect(page.locator(`[id="${study}-groups-cell"]`)).toContainText(group);

    // check if Phenotype browser is enabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).not.toContainClass('disabled-download');

    // remove any_user from list of groups of the pheno study
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await page.getByRole('tab', { name: 'Datasets' }).click();
    await searchInTable(page, study);
    await page.locator(`[id="${study}-groups-cell"] [id="${group}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(`[id="${group}-datasets-cell"] [id="${study}-list-item"]`)).not.toBeVisible();
  });

  test('should give rights for pheno_helloworld to researcher', async({ page }) => {
    const study = utils.datasetIds.phenoHelloWorld;
    const researcher = 'research@iossifovlab.com';

    // check if Phenotype browser download is disabled when no user is logged in
    await utils.logout(page);
    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).toContainClass('disabled-download');

    // add pheno group to reasearcher
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"]`).getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await searchInMenu(page, study);
    await page.waitForSelector(`button:text("${study}")`);
    await page.getByRole('button', { name: study }).click();

    await utils.logout(page);
    // check if Phenotype browser download is enabled when researcher is logged in
    await utils.login(page, researcher, 'secret');

    await utils.navigateToDataset(page, study);
    await expect(page.locator('gpf-pheno-browser')).toBeVisible();
    await expect(page.locator('#download-measures')).not.toContainClass('disabled-download');

    // remove pheno group from groups list of research
    await utils.logout(page);
    await utils.loginAdmin(page);
    await page.locator('a:text("Management")').click();
    await searchInTable(page, researcher);

    await page.locator(`[id="${researcher}-groups-cell"] [id="${study}-list-item"] gpf-confirm-button`).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();

    await expect(page.locator(`[id="${researcher}-groups-cell"]`)).not.toContainText(study);
  });
});

async function searchInTable(page: Page, name: string): Promise<void> {
  await page.locator('#search-field').clear();
  await page.locator('#search-field').focus();
  await page.keyboard.type(name);
}

async function searchInMenu(page: Page, name: string): Promise<void> {
  await page.getByRole('textbox', { name: 'Search' }).clear();
  await page.getByRole('textbox', { name: 'Search' }).focus();
  await page.keyboard.type(name);
}