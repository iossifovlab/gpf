import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { HomePage } from './pages/home.page';
import { GeneProfilesSingleView } from './components/gene-profiles-single-view.component';

// tb-nxl-fix: the 'Home page description tests' describe that used to
// live here (2 tests writing the global /api/v3/instance/description
// file via #edit-icon — admin-only) moved to user-management.spec.ts.
// loginWorkerUser users have no admin group, so #edit-icon never
// appears for them; build #28 surfaced this as 'should add description'
// failing and the .serial sibling getting skipped. user-management.spec
// owns the file-level serial worker that all admin Management/edit
// writes share.

test.describe('Home page tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(`${utils.frontendUrl}/home`, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await page.waitForSelector('gpf-home');
  });

  test('should navigate to Gene profiles', async({ page }) => {
    const homePage = new HomePage(page);
    await expect(homePage.geneProfilesSection).toBeVisible();

    await homePage.allGenes.click();
    await expect(homePage.header.navLink('Gene Profiles')).toHaveClass('highlighted-route');
    await expect(homePage.root).not.toBeVisible();
    await expect(homePage.geneProfilesBlock).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles`);
  });

  test('should search genes by selecting gene', async({ page }) => {
    const homePage = new HomePage(page);
    const singleView = new GeneProfilesSingleView(page);
    await homePage.searchBox.focus();
    await page.keyboard.type('chd');
    await homePage.option('CHD8').click();

    await expect(homePage.header.navLink('Gene Profiles')).toHaveClass('highlighted-route');
    await expect(homePage.root).not.toBeVisible();
    await expect(homePage.geneProfilesSingleView).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(singleView.tab('CHD8')).toBeVisible();
    await expect(singleView.headingFor('CHD8')).toBeVisible();
  });

  test('should search genes by typing gene', async({ page }) => {
    const homePage = new HomePage(page);
    const singleView = new GeneProfilesSingleView(page);
    await homePage.searchBox.focus();
    await page.keyboard.type('chd8');
    await expect(homePage.option('CHD8')).toBeVisible();
    await page.keyboard.press('Enter');

    await expect(homePage.header.navLink('Gene Profiles')).toHaveClass('highlighted-route');
    await expect(homePage.root).not.toBeVisible();
    await expect(homePage.geneProfilesSingleView).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(singleView.tab('CHD8')).toBeVisible();
    await expect(singleView.headingFor('CHD8')).toBeVisible();
  });

  test('should show error message when searching invalid gene', async({ page }) => {
    const homePage = new HomePage(page);
    await homePage.searchBox.focus();
    await page.keyboard.type('chd88');
    await page.waitForResponse(
      resp => resp.url().includes('api/v3/gene_profiles/table/gene_symbols') && resp.status() === 200
    );
    await page.keyboard.press('Enter');

    await expect(homePage.noGeneFound).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);
  });

  test('should expand and close datasets', async({ page }) => {
    const homePage = new HomePage(page);
    await expect(homePage.datasetLink('pheno_helloworld')).toBeVisible();
    await expect(homePage.datasetLink('ALL Genotypes')).toBeVisible();
    await expect(homePage.datasetLink('comp_all_liftover')).toBeVisible();
    await expect(homePage.datasetLink('COMP Genotypes')).toBeVisible();
    await expect(homePage.datasetLink('multi_liftover')).toBeVisible();
    await expect(homePage.datasetLink('iossifov_2014_liftover')).toBeVisible();
    await expect(homePage.datasetLink('Hello World Genotypes')).toBeVisible();

    await expect(homePage.datasetLink('comp_denovo_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('comp_vcf_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('denovo_helloworld')).not.toBeVisible();
    await expect(homePage.datasetLink('vcf_helloworld')).not.toBeVisible();

    await homePage.collapseIcons.nth(1).click();
    await expect(homePage.datasetLink('denovo_helloworld')).toBeVisible();
    await expect(homePage.datasetLink('vcf_helloworld')).toBeVisible();

    await homePage.collapseIcons.nth(2).click();
    await expect(homePage.datasetLink('comp_denovo_liftover')).toBeVisible();
    await expect(homePage.datasetLink('comp_vcf_liftover')).toBeVisible();

    await homePage.collapseIcons.nth(0).click();
    await expect(homePage.datasetLink('pheno_helloworld')).toBeVisible();
    await expect(homePage.datasetLink('ALL Genotypes')).toBeVisible();
    await expect(homePage.datasetLink('comp_all_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('COMP Genotypes')).not.toBeVisible();
    await expect(homePage.datasetLink('multi_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('iossifov_2014_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('comp_denovo_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('comp_vcf_liftover')).not.toBeVisible();
    await expect(homePage.datasetLink('denovo_helloworld')).not.toBeVisible();
    await expect(homePage.datasetLink('vcf_helloworld')).not.toBeVisible();
  });


  test('should navigate to dataset and check icons', async({ page }) => {
    const homePage = new HomePage(page);

    await homePage.datasetLink('Hello World Genotypes').click();
    await expect(homePage.header.navLink('Datasets')).toHaveClass('highlighted-route');
    await expect(homePage.root).not.toBeVisible();
    await expect(homePage.geneBrowser).toBeVisible();

    await expect(homePage.selectedDatasetName).toHaveText('Hello World Genotypes');
    await expect(homePage.datasets.dropdownButton)
      .toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(homePage.datasets.dropdownButtonIcon('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(homePage.datasets.dropdownButtonIcon('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(homePage.datasets.dropdownButtonIcon('.transmitted-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(homePage.datasets.dropdownButtonIcon('.phenotype-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
  });


  test('list of icons of different datasets in home page', async({ page }) => {
    const homePage = new HomePage(page);

    await homePage.collapseIcons.nth(1).click();

    await expect(homePage.iconsWrapper('denovo_helloworld')).toHaveText('geneticskid_starhow_to_reg');
    await expect(homePage.iconsWrapper('vcf_helloworld')).toHaveText('family_historyhow_to_reg');
    await expect(homePage.iconsWrapper('iossifov_2014_liftover')).toHaveText('geneticskid_star');
    await expect(homePage.iconsWrapper('pheno_helloworld')).toHaveText('how_to_reg');
    await expect(homePage.iconsWrapper('ALL_genotypes')).toHaveText('geneticskid_starfamily_history');
  });

  test('colors of icons of Hello World Genotypes in home page when user has no access rights', async({ page }) => {
    await utils.logout(page);
    const homePage = new HomePage(page);

    const helloWorldGenotypesIcons = homePage.iconsWrapper('helloworld_genotypes');
    await expect(helloWorldGenotypesIcons).toHaveText('geneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypesIcons.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypesIcons.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypesIcons.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(helloWorldGenotypesIcons.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');

    await utils.loginWorkerUser(page);

    await expect(helloWorldGenotypesIcons).toHaveText('geneticskid_starfamily_historyhow_to_reg');
    await expect(helloWorldGenotypesIcons.locator('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypesIcons.locator('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypesIcons.locator('.transmitted-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(helloWorldGenotypesIcons.locator('.phenotype-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  test('should navigate from home page to dataset and check icons when user has no access rights', async({ page }) => {
    const homePage = new HomePage(page);

    await utils.logout(page);
    await homePage.datasetLink('Hello World Genotypes').click();
    await expect(homePage.header.navLink('Datasets')).toHaveClass('highlighted-route');
    await expect(homePage.root).not.toBeVisible();
    await expect(homePage.geneBrowser).toBeVisible();
    await expect(homePage.registerAlert).toBeVisible();
    await expect(homePage.selectedDatasetName).toHaveText('Hello World Genotypes');
    await expect(homePage.datasets.dropdownButton)
      .toHaveText('Hello World Genotypesgeneticskid_starfamily_historyhow_to_reg');
    await expect(homePage.datasets.dropdownButtonIcon('.denovo-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(homePage.datasets.dropdownButtonIcon('.star-icon')).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(homePage.datasets.dropdownButtonIcon('.transmitted-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(homePage.datasets.dropdownButtonIcon('.phenotype-icon')).toHaveCSS('color', 'rgb(220, 220, 220)');
  });
});
