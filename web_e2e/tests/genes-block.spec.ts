
import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Genes block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'comp_all', 'Genotype browser');
  });

  test('should display gene symbols panel', async({ page }) => {
    await expect(page.locator('#gene-symbols-panel')).toBeHidden();

    await page.click('#gene-symbols');
    await expect(page.locator('#gene-symbols-panel')).toBeVisible();
  });

  test('should display error alert in gene symbols panel when the textarea is empty', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Symbols' }).click();
    await expect(page.getByRole('alert')).toBeVisible();

    await page.fill('textarea', 'SAMD11');
    await expect(page.locator('css=.warning-alert')).toBeHidden();
  });

  test('should display gene sets panel', async({ page }) => {
    await expect(page.locator('.gene-sets-panel')).toBeHidden();
    await page.getByRole('tab', { name: 'Gene Sets' }).click();
    await expect(page.locator('#gene-sets-panel')).toBeVisible();
  });

  test('should display error alert in gene sets panel when the textarea is empty', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Sets' }).click();
    await expect(page.locator('css=.alert-danger')).toBeVisible();

    await page.click('input#search-box');
    await page.fill('input#search-box', 'non-essential genes');

    await page.getByText('non-essential genes').click();
    await expect(page.locator('css=.alert-danger')).not.toBeVisible();
  });

  test('should display gene weights panel', async({ page }) => {
    await expect(page.locator('#gene-scores-panel')).toBeHidden();

    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await expect(page.locator('#gene-scores-panel')).toBeVisible();
  });
});
