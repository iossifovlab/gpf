import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { RegionsBlock } from './components/regions-block.component';

test.describe('Regions block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display regions filter panel', async({ page }) => {
    const regionsBlock = new RegionsBlock(page);
    await expect(regionsBlock.filterPanel).not.toBeVisible();
    await regionsBlock.regionsFilterToggle.click();
    await expect(regionsBlock.filterPanel).toBeVisible();
  });


  test('should display error alert in regions panel when the textarea is empty', async({ page }) => {
    const regionsBlock = new RegionsBlock(page);
    await regionsBlock.regionsFilterToggle.click();
    await expect(regionsBlock.emptyError).toBeVisible();

    await regionsBlock.textarea.pressSequentially('14:21393485');
    await expect(regionsBlock.invalidRegionError('14:21393485')).toBeVisible();

    await regionsBlock.textarea.clear();
    await regionsBlock.textarea.pressSequentially('chr14:21393485');
    await expect(regionsBlock.errorsAlert).not.toBeVisible();
  });
});
