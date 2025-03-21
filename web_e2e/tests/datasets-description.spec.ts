import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Dataset description tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Dataset description');
  });

  test('should display dataset description window', async({ page }) => {
    await expect(page.locator('gpf-dataset-description')).toBeVisible();
  });

  test('should display empty description placeholder text', async({ page }) => {
    await expect(page.locator('#empty-description')).toBeVisible();
    await expect(
      page.locator('#empty-description')
    ).toHaveText('Empty description. Write a description using the pencil button to the right.');
  });

  test('should display edit icon', async({ page }) => {
    await expect(page.locator('#edit-icon')).toBeVisible();
  });

  test('should display angular markdown editor after clicking the edit button', async({ page }) => {
    await expect(page.locator('.editor')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('.editor')).toBeVisible();
  });

  test('should display preview button', async({ page }) => {
    await expect(page.getByText('Preview')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Preview')).toBeVisible();
  });

  test('should display save button', async({ page }) => {
    await expect(page.getByText('Save')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Save')).toBeVisible();
  });

  test('should display close button', async({ page }) => {
    await expect(page.getByText('Close')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.getByText('Close')).toBeVisible();
  });

  test('should display the editor header bar', async({ page }) => {
    await expect(page.locator('.md-header')).not.toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('.md-header')).toBeVisible();
  });

  test('should hide the edit button after clicking it', async({ page }) => {
    await expect(page.locator('#edit-icon')).toBeVisible();
    await page.locator('#edit-icon').click();
    await expect(page.locator('#edit-icon')).not.toBeVisible();
    await page.getByText('Close').click();
    await expect(page.locator('#edit-icon')).toBeVisible();
  });

  test('should save the markdown', async({ page }) => {
    await expect(page.locator('#empty-description')).toBeVisible();
    await expect(page.locator('markdown p')).not.toBeVisible();

    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').type('TEST DESCRIPTION ASDF');
    await page.getByText('Save').click();
    await expect(page.locator('markdown p')).toHaveText('TEST DESCRIPTION ASDF');
    await expect(page.locator('#empty-description')).not.toBeVisible();

    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('');
    await page.getByText('Save').click();
    await expect(page.locator('#empty-description')).toBeVisible();
  });
});

test.describe('Dataset description access rights tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
  });

  test('should always show the dataset description button if the user is admin', async({ page }) => {
    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    await expect(page.getByText('Dataset Description')).toBeVisible();
    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    await expect(page.getByText('Dataset Description')).toBeVisible();
  });
  test('should NOT show the dataset description button for a regular user when no description is available', async({
    page
  }) => {
    await utils.navigateToDataset(page, utils.datasetIds.allGenotypes);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.denovoHelloWorld);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.helloWorldGenotypes);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.vcfHelloWorld);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.phenoHelloWorld);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.iossifov2014Liftover);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);

    await utils.navigateToDataset(page, utils.datasetIds.multiLiftover);
    expect(await page.getByText('Dataset Description').getAttribute('pointer-events')).toBe(null);
  });

  test('should log admin, give researcher user access rights for iossifov_2014,' +
       'create dataset description for iossifov_2014, log researcher user and check ' +
       'whether the newly created description exists and that it cannot be edited', async({ page }) => {
    await page.locator('a:text("Management")').click();

    await page.locator('[id="user_iossifov_2014@iossifovlab.com-groups-cell"]').getByText('Add').click();
    await page.waitForSelector('.add-item-button');
    await page.getByRole('textbox', { name: 'Search' }).focus();
    await page.keyboard.type('iossifov_2014_liftover');
    await page.waitForSelector('button:text("iossifov_2014_liftover")');
    await page.getByRole('button', { name: 'iossifov_2014_liftover' }).click();
    await page.mouse.click(0, 0); // close the menu

    await page.locator('#header a:text("Datasets")').click();
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('IOSSIFOV TEST DESCRIPTION');
    await page.getByText('Save').click();
    await utils.logout(page);

    await utils.login(page, 'user_iossifov_2014@iossifovlab.com');
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    await expect(page.locator('markdown p')).toHaveText('IOSSIFOV TEST DESCRIPTION');
    await expect(page.locator('#edit-icon')).not.toBeVisible();
    await utils.logout(page);

    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Dataset description');
    await page.locator('#edit-icon').click();
    await page.locator('.editor textarea').fill('');
    await page.getByText('Save').click();

    await page.locator('a:text("Management")').click();
    await page.locator(
      '[id="user_iossifov_2014@iossifovlab.com-groups-cell"] #iossifov_2014_liftover-list-item gpf-confirm-button'
    ).click();
    await page.getByRole('button', { name: 'Remove', exact: true }).click();
    await expect(page.locator(
      '[id="user_iossifov_2014@iossifovlab.com-groups-cell"]')
    ).not.toContainText('iossifov_2014_liftover');
  });

  test('should login regular user, try to navigate to a dataset description page without description via the url ' +
  'and get redirected back to the home page', async({ page }) => {
    const homePageUrl = `${utils.frontendUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.datasetDescription}`;
    const datasetDescriptionUrl =
      `${utils.frontendUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.datasetDescription}`;

    await page.goto(datasetDescriptionUrl);
    expect(page.url()).toBe(homePageUrl);
  });
});
