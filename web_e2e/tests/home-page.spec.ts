import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Home page tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(`${utils.frontendUrl}/home`, {waitUntil: 'load'});
    await utils.login(page);
    await page.waitForSelector('gpf-home');
  });

  test('should add description', async({ page }) => {
    await page.locator('#edit-icon').click();
    await expect(page.locator('.editor')).toBeVisible();
    await page.locator('gpf-markdown-editor').locator('textarea').fill('Test description');
    await page.getByText('Save').click();

    await expect(page.locator('.editor')).not.toBeVisible();
    await page.reload();
    await expect(page.locator('#edit-container p')).toHaveText('Test description');

    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').clear();
    await page.getByText('Save').click();
  });

  test('should check if editing description is disabled when no access rights', async({ page }) => {
    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').fill('Test description');
    await page.getByText('Save').click();
    await page.reload();

    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(page.locator('#edit-container p')).toHaveText('Test description');
    await expect(page.locator('#edit-icon')).not.toBeVisible();

    await utils.login(page);
    await page.waitForSelector('gpf-home');
    await page.locator('#edit-icon').click();
    await page.locator('gpf-markdown-editor').locator('textarea').clear();
    await page.getByText('Save').click();

    await page.reload();
    await page.waitForSelector('gpf-home');
    await expect(page.locator('#empty-description')).toBeVisible();
  });

  test('should no show empty description with no access rights', async({ page }) => {
    await utils.logout(page);
    await page.waitForSelector('gpf-home');
    await expect(page.locator('gpf-markdown-editor')).not.toBeVisible();

    await utils.login(page);
    await page.waitForSelector('gpf-home');
    await expect(page.locator('gpf-markdown-editor')).toBeVisible();
  });

  test('should navigate to Gene profiles', async({ page }) => {
    await expect(page.locator('#gene-profiles-section')).toBeVisible();

    await page.getByText('All genes').click();
    await expect(page.locator('a:text("Gene Profiles")')).toHaveClass('highlighted-route');
    await expect(page.locator('gpf-home')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-block')).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles`);
  });

  test('should search genes by selecting gene', async({ page }) => {
    await page.locator('#search-box').focus();
    await page.keyboard.type('chd');
    await page.getByRole('option', {name: 'CHD8'}).click();

    await expect(page.locator('a:text("Gene Profiles")')).toHaveClass('highlighted-route');
    await expect(page.locator('gpf-home')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(page.locator('.tab').getByText('CHD8')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'CHD8' })).toBeVisible();
  });

  test('should search genes by typing gene', async({ page }) => {
    await page.locator('#search-box').focus();
    await page.keyboard.type('chd8');
    await expect(page.getByRole('option', {name: 'CHD8'})).toBeVisible();
    await page.keyboard.press('Enter');

    await expect(page.locator('a:text("Gene Profiles")')).toHaveClass('highlighted-route');
    await expect(page.locator('gpf-home')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(page.locator('.tab').getByText('CHD8')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'CHD8' })).toBeVisible();
  });

  test('should show error message when searching invalid gene', async({ page }) => {
    await page.locator('#search-box').focus();
    await page.keyboard.type('chd88');
    await page.waitForResponse(
      resp => resp.url().includes('api/v3/gene_profiles/table/gene_symbols') && resp.status() === 200
    );
    await page.keyboard.press('Enter');

    await expect(page.getByText('No such gene found!')).toBeVisible();
    await expect(page).toHaveURL(`${utils.frontendUrl}/home`);
  });

  test('should expand and close datasets', async({ page }) => {
    await expect(page.locator('a:text("pheno_helloworld")')).toBeVisible();
    await expect(page.locator('a:text("comp_pheno")')).toBeVisible();
    await expect(page.locator('a:text("ALL Genotypes")')).toBeVisible();
    await expect(page.locator('a:text("comp_all_liftover")')).toBeVisible();
    await expect(page.locator('a:text("COMP Genotypes")')).toBeVisible();
    await expect(page.locator('a:text("multi_liftover")')).toBeVisible();
    await expect(page.locator('a:text("iossifov_2014_liftover")')).toBeVisible();
    await expect(page.locator('a:text("Hello World Genotypes")')).toBeVisible();

    await expect(page.locator('a:text("comp_denovo_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("comp_vcf_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("denovo_helloworld")')).not.toBeVisible();
    await expect(page.locator('a:text("vcf_helloworld")')).not.toBeVisible();

    await page.locator('.collapse-dataset-icon').nth(1).click();
    await expect(page.locator('a:text("denovo_helloworld")')).toBeVisible();
    await expect(page.locator('a:text("vcf_helloworld")')).toBeVisible();

    await page.locator('.collapse-dataset-icon').nth(2).click();
    await expect(page.locator('a:text("comp_denovo_liftover")')).toBeVisible();
    await expect(page.locator('a:text("comp_vcf_liftover")')).toBeVisible();

    await page.locator('.collapse-dataset-icon').nth(0).click();
    await expect(page.locator('a:text("pheno_helloworld")')).toBeVisible();
    await expect(page.locator('a:text("comp_pheno")')).toBeVisible();
    await expect(page.locator('a:text("ALL Genotypes")')).toBeVisible();
    await expect(page.locator('a:text("comp_all_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("COMP Genotypes")')).not.toBeVisible();
    await expect(page.locator('a:text("multi_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("iossifov_2014_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("comp_denovo_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("comp_vcf_liftover")')).not.toBeVisible();
    await expect(page.locator('a:text("denovo_helloworld")')).not.toBeVisible();
    await expect(page.locator('a:text("vcf_helloworld")')).not.toBeVisible();
  });


  test('should navigate to dataset', async({ page }) => {
    await page.locator('a:text("Hello World Genotypes")').click();
    await expect(page.locator('a:text("Datasets")')).toHaveClass('highlighted-route');
    await expect(page.locator('gpf-home')).not.toBeVisible();
    await expect(page.locator('gpf-gene-browser')).toBeVisible();
    await expect(page.locator('#datasets-dropdown-menu-button')).toHaveText('Hello World Genotypes');
  });
});