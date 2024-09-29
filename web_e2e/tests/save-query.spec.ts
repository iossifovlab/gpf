import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Save query common tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', 'dropdown-menu');
    await page.locator('#save-query-dropdown-button').click();
  });

  test('should display save query elements', async({ page }) => {
    await expect(page.locator('#link-input')).toBeVisible();
    await expect(page.locator('#copy-link-button')).toBeVisible();
    await expect(page.locator('gpf-save-query #name')).toBeVisible();
    await expect(page.locator('gpf-save-query #description')).toBeVisible();
    await expect(page.locator('gpf-save-query #save-button')).toBeVisible();
  });
});

test.describe('Save query tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
  });

  test('should open save query dropdown menu after pressing "Share/save query" button', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', /dropdown-menu/);

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#save-query-dropdown')).toHaveAttribute('class', /dropdown-menu show/);
  });

  test('should open save query dropdown menu, click on the copy link button ' +
     'and check whether the "Copied!" tooltip appears', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#copy-link-button')).toBeVisible();

    await expect(page.locator('ngb-tooltip-window')).not.toBeVisible();
    await page.locator('#copy-link-button').click();
    await expect(page.locator('ngb-tooltip-window')).toBeVisible();
  });

  test('should save a query, load it, open all tools tabs and delete the query', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await page.locator('#save-query-dropdown-button').click();
    await page.locator('gpf-save-query #name').fill('TestLoadAndDeleteQuery');
    await page.locator('gpf-save-query #save-button').click();
    await page.waitForResponse(utils.backendUrl + '/api/v3/user_queries/save');
    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});
    const cell = page.locator('div[id="query-TestLoadAndDeleteQuery-actions-cell"]').first();
    await expect(cell).toBeVisible();
    await cell.locator('#load-button').click();

    await page.locator('li.nav-item').filter({ hasText: 'Dataset Statistics'}).click();
    await expect(page.locator('gpf-variant-reports')).toBeVisible();
    await page.locator('li.nav-item').filter({ hasText: 'Genotype browser'}).click();
    await expect(page.locator('gpf-genotype-browser')).toBeVisible();
    await page.locator('li.nav-item').filter({ hasText: 'Phenotype browser'}).click();
    await expect(page.locator('gpf-pheno-browser-table')).toBeVisible();
    await page.locator('li.nav-item').filter({ hasText: 'Phenotype tool'}).click();
    await expect(page.locator('gpf-pheno-tool')).toBeVisible();
    await page.locator('li.nav-item').filter({ hasText: 'Gene browser'}).click();
    await expect(page.locator('gpf-gene-browser')).toBeVisible();

    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});

    await cell.locator('#delete-button').click();
  });

  test('should navigate to genotype browser, check all effect types checkboxes, save a query, ' +
  'load it and validate that all effect types checkboxes are checked', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await page.locator('gpf-effect-types').getByText('All').click();
    await page.locator('#save-query-dropdown-button').click();
    await page.locator('gpf-save-query #name').fill('CheckedSavedQuery');
    await expect(page.locator('gpf-save-query #save-button')).toBeVisible();
    await page.locator('gpf-save-query #save-button').click({force: true});
    await page.waitForResponse(utils.backendUrl + '/api/v3/user_queries/save');

    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});
    await page.waitForSelector('div#query-CheckedSavedQuery-actions-cell');
    const cell = page.locator('div#query-CheckedSavedQuery-actions-cell').first();
    await expect(cell).toBeVisible();
    await cell.locator('#load-button').click();

    const radios = page.locator('gpf-effect-types input');
    await expect(page.getByText('nonsense')).toBeChecked();
    const radiosPromises = [];
    const count = await radios.count();
    for (let i = 0; i < count; i++) {
      radiosPromises.push(radios.nth(i).isChecked());
    }

    await Promise.all(radiosPromises).then(results => {
      for (let i = 0; i < results.length; i++) {
        expect(results[i]).toBe(true);
      }
    });

    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});
    await cell.locator('#delete-button').click();
  });


  test('should navigate to genotype browser, check all effect types checkboxes, click on "Save/share query" button, ' +
  'copy the share link, load it and validate that all effect types checkboxes are checked', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await page.locator('gpf-effect-types').getByText('All').click();
    await page.locator('#save-query-dropdown-button').click();

    await expect(page.locator('#link-input')).not.toHaveValue('');
    const url = await page.locator('#link-input').inputValue();
    await page.goto(url);
    await page.waitForSelector('gpf-genotype-browser');

    const radios = page.locator('gpf-effect-types input');
    await expect(page.getByText('nonsense')).toBeChecked();
    const radiosPromises = [];
    const count = await radios.count();
    for (let i = 0; i < count; i++) {
      radiosPromises.push(radios.nth(i).isChecked());
    }

    await Promise.all(radiosPromises).then(results => {
      for (let i = 0; i < results.length; i++) {
        expect(results[i]).toBe(true);
      }
    });
  });
});

