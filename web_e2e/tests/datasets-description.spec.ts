import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { Datasets } from './components/datasets.component';

// tb-nxl-fix: the 'Dataset description tests' describe that used to live
// here (10 tests, all admin-only — #edit-icon, #empty-description
// placeholder, save the markdown) moved to user-management.spec.ts.
// All of them needed admin to render the editor controls; under
// loginWorkerUser the placeholder/edit-icon don't appear, and a single
// failure cascaded the rest of the .serial describe into skipped
// (build #28). The remaining tests below are non-admin: they assert
// the regular-user / unauthenticated UI surface around dataset
// descriptions, so loginWorkerUser is the right login here.

test.describe('Dataset description access rights tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
  });

  test('should always show the dataset description button if the user is admin', async({ page }) => {
    const datasets = new Datasets(page);
    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(datasets.datasetDescriptionButton).toBeVisible();
  });
  test('should NOT show the dataset description button for a regular user when no description is available', async({
    page
  }) => {
    const datasets = new Datasets(page);
    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    expect(await datasets.datasetDescriptionButton.getAttribute('pointer-events')).toBe(null);
  });

  // tb-nxl-fix: the admin-only "should log admin, give researcher user
  // access rights for iossifov_2014..." test moved to
  // user-management.spec.ts — it writes Management state and writes a
  // description on iossifov_2014_liftover, both of which need the
  // file-level serial admin worker.

  test('should login regular user, try to navigate to a dataset description page without description via the url ' +
  'and get redirected back to the home page', async({ page }) => {
    const homePageUrl = `${utils.frontendUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.datasetDescription}`;
    const datasetDescriptionUrl =
      `${utils.frontendUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.datasetDescription}`;

    await page.goto(datasetDescriptionUrl);
    expect(page.url()).toBe(homePageUrl);
  });
});
