import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { GeneBrowser } from './components/gene-browser.component';
import { UniqueFamilyVariantsFilter } from './components/unique-family-variants-filter.component';

test.describe('Unique family variants filter tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
  });

  test('should disable unique family variants filter on a study', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    const uniqueFamilyVariants = new UniqueFamilyVariantsFilter(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype Browser');
    await expect(uniqueFamilyVariants.block).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.vcfHelloWorld, 'Gene Browser');
    await geneBrowser.searchGene('CHD8');
    await expect(geneBrowser.genePlot).toBeVisible();
    await expect(uniqueFamilyVariants.checkbox).toBeDisabled();
  });

  test('should disable unique family variants when no variants are loaded', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    const uniqueFamilyVariants = new UniqueFamilyVariantsFilter(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Gene Browser');
    await geneBrowser.searchGene('CSDC2');
    await expect(geneBrowser.genePlot).toBeVisible();
    await expect(uniqueFamilyVariants.checkbox).toBeDisabled();
  });

  test('should enable the unique family variants filter on a dataset with at least 2 studies inside', async({
    page
  }) => {
    const geneBrowser = new GeneBrowser(page);
    const uniqueFamilyVariants = new UniqueFamilyVariantsFilter(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype Browser');
    await expect(uniqueFamilyVariants.block).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Gene Browser');
    await geneBrowser.searchGene('CHD8');
    await expect(geneBrowser.genePlot).toBeVisible();
    await expect(uniqueFamilyVariants.checkbox).toBeEnabled();
  });

  test('should use the unique family variants filter to hide variants', async({ page }) => {
    const geneBrowser = new GeneBrowser(page);
    const uniqueFamilyVariants = new UniqueFamilyVariantsFilter(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype Browser');
    await expect(uniqueFamilyVariants.block).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Gene Browser');
    await geneBrowser.searchGene('CHD8');
    await expect(geneBrowser.genePlot).toBeVisible();

    await expect(uniqueFamilyVariants.variantsCountSpan).toHaveText('25 variants selected');
    await uniqueFamilyVariants.checkbox.click();
    await expect(uniqueFamilyVariants.variantsCountSpan).toHaveText('22 variants selected');
  });
});
