import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { SaveQuery } from './components/save-query.component';
import { EffectTypes } from './components/effect-types.component';
import { Header } from './components/header.component';
import { Datasets } from './components/datasets.component';

test.describe('Save query common tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    const saveQueryComponent = new SaveQuery(page);
    await expect(saveQueryComponent.dropdown).toHaveAttribute('class', 'dropdown-menu');
    await saveQueryComponent.dropdownButton.click();
  });

  test('should display save query elements', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    await expect(saveQueryComponent.linkInput).toBeVisible();
    await expect(saveQueryComponent.copyLinkButton).toBeVisible();
    await expect(saveQueryComponent.nameInput).toBeVisible();
    await expect(saveQueryComponent.descriptionInput).toBeVisible();
    await expect(saveQueryComponent.saveButton).toBeVisible();
  });
});

test.describe('Save query tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);
  });

  test('should open save query dropdown menu after pressing "Share/save query" button', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    await expect(saveQueryComponent.dropdown).toHaveAttribute('class', /dropdown-menu/);

    await saveQueryComponent.dropdownButton.click();
    await expect(saveQueryComponent.dropdown).toHaveAttribute('class', /dropdown-menu show/);
  });

  test('should open save query dropdown menu, click on the copy link button ' +
     'and check whether the "Copied!" tooltip appears', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    await saveQueryComponent.dropdownButton.click();
    await expect(saveQueryComponent.copyLinkButton).toBeVisible();

    await expect(saveQueryComponent.copiedTooltip).not.toBeVisible();
    await saveQueryComponent.copyLinkButton.click();
    await expect(saveQueryComponent.copiedTooltip).toBeVisible();
  });

  test('should save a query, load it, open all tools tabs and delete the query', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    const header = new Header(page);
    const datasets = new Datasets(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    await saveQueryComponent.dropdownButton.click();
    await saveQueryComponent.nameInput.fill('TestLoadAndDeleteQuery');
    await saveQueryComponent.saveButton.click();
    await page.waitForResponse(utils.backendUrl + '/api/v3/user_queries/save');
    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});
    await expect(saveQueryComponent.savedQueryCell('TestLoadAndDeleteQuery')).toBeVisible();
    await saveQueryComponent.loadButton('TestLoadAndDeleteQuery').click();

    await header.toolNavItem('Dataset Statistics').click();
    await expect(datasets.variantReports).toBeVisible();
    await header.toolNavItem('Genotype browser').click();
    await expect(datasets.genotypeBrowser).toBeVisible();
    await header.toolNavItem('Phenotype browser').click();
    await expect(datasets.phenoBrowserTable).toBeVisible();
    await header.toolNavItem('Phenotype tool').click();
    await expect(datasets.phenoTool).toBeVisible();
    await header.toolNavItem('Gene browser').click();
    await expect(datasets.geneBrowser).toBeVisible();

    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});

    await saveQueryComponent.deleteButton('TestLoadAndDeleteQuery').click();
  });

  test('should navigate to genotype browser, check all effect types checkboxes, save a query, ' +
  'load it and validate that all effect types checkboxes are checked', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    const effectTypesComponent = new EffectTypes(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    await effectTypesComponent.clickButton('All');
    await saveQueryComponent.dropdownButton.click();
    await saveQueryComponent.nameInput.fill('CheckedSavedQuery');
    await expect(saveQueryComponent.saveButton).toBeVisible();
    await saveQueryComponent.saveButton.click({force: true});
    await page.waitForResponse(utils.backendUrl + '/api/v3/user_queries/save');

    await page.goto(utils.frontendUrl + '/user-profile', { waitUntil: 'load'});
    await page.waitForSelector('div#query-CheckedSavedQuery-actions-cell');

    await expect(saveQueryComponent.savedQueryCell('CheckedSavedQuery')).toBeVisible();
    await saveQueryComponent.loadButton('CheckedSavedQuery').click();

    const radios = effectTypesComponent.checkboxes;
    await expect(effectTypesComponent.label('nonsense')).toBeChecked();
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
    await saveQueryComponent.deleteButton('CheckedSavedQuery').click();
  });


  test('should navigate to genotype browser, check all effect types checkboxes, click on "Save/share query" button, ' +
  'copy the share link, load it and validate that all effect types checkboxes are checked', async({ page }) => {
    const saveQueryComponent = new SaveQuery(page);
    const effectTypesComponent = new EffectTypes(page);

    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Genotype browser');
    await effectTypesComponent.clickButton('All');
    await saveQueryComponent.dropdownButton.click();

    await expect(saveQueryComponent.linkInput).not.toHaveValue('');
    const url = await saveQueryComponent.linkInput.inputValue();
    await page.goto(url);
    await page.waitForSelector('gpf-genotype-browser');

    const radios = effectTypesComponent.checkboxes;
    await expect(effectTypesComponent.label('nonsense')).toBeChecked();
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
