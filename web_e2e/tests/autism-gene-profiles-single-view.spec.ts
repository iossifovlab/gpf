import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('Autism gene profiles single view tests', () => {
  let CHD8Page: Page;
  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToSidenavPage(page, 'autism-gene-profiles');
    await page.locator('input#gene-search-input').fill('CHD8');
    const pagePromise = context.waitForEvent('page');
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();

    CHD8Page = await pagePromise;
    await CHD8Page.waitForLoadState();
  });


  test('should display header', async({ context }) => {
    const targetPage = context.pages()[1];
    expect(targetPage.locator('gpf-autism-gene-profile-single-view h2')).toBeTruthy();
    await expect(targetPage.locator('gpf-autism-gene-profile-single-view h2')).toHaveText('CHD8');
  });

  test('should display the autism scores table', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('#autism_scores')).toBeVisible();
    await expect(targetPage.locator('#autism_scores th')).toHaveText('Autism Scores');
    expect(await targetPage.locator('#autism_scores tr').count()).toBe(1);
  });


  test('should display the protection scores table', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('#protection_scores')).toBeVisible();
    await expect(targetPage.locator('#protection_scores th')).toHaveText('Protection Scores');
    await expect(targetPage.locator('#protection_scores tr')).toHaveCount(4);
  });


  test('should display the single scores markers', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('.single-score-marker')).toHaveCount(5);
  });


  test('should display the autism gene sets table', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('#autism_gene_sets')).toBeVisible();
    await expect(targetPage.locator('#autism_gene_sets th')).toHaveText('Autism Gene Sets');
    await expect(targetPage.locator('#autism_gene_sets tr')).toHaveCount(2);
  });


  test('should display the relevant gene sets table', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('#relevant_gene_sets')).toBeVisible();
    await expect(targetPage.locator('#relevant_gene_sets th')).toHaveText('Relevant Gene Sets');
    await expect(targetPage.locator('#relevant_gene_sets tr')).toHaveCount(4);
  });

  test('should display the datasets table', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('.datasets-table')).toBeVisible();
    await expect(targetPage.locator('.datasets-table th').first()).toHaveText('iossifov_2014');
    await expect(targetPage.locator('.datasets-table tr')).toHaveCount(5);
  });
});

test.describe('Autism gene profiles single view links tests', () => {
  let CHD8Page: Page;
  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToSidenavPage(page, 'autism-gene-profiles');
    await page.locator('input#gene-search-input').fill('CHD8');
    const pagePromise = context.waitForEvent('page');
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();

    CHD8Page = await pagePromise;
    await CHD8Page.waitForLoadState();
  });

  test('should display gene browser link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('#gene-browser-link')).toBeVisible();
    await expect(targetPage.locator('#gene-browser-link')).toHaveText('Gene Browser');
  });

  test('should display UCSC link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('a.link-external-page').filter({ hasText: 'UCSC genome browser'})).toBeVisible();
    await expect(targetPage.locator('a.link-external-page').filter(
      { hasText: 'UCSC genome browser'}
    )).toBeVisible();
  });

  test('should display GeneCards link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('a.link-external-page').filter({ hasText: 'GeneCards' })).toBeVisible();
    await expect(targetPage.locator('a.link-external-page').filter({ hasText: 'GeneCards' })).toHaveText('GeneCards');
  });

  test('should display Pubmed link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.locator('a.link-external-page').filter({ hasText: 'Pubmed' })).toBeVisible();
    await expect(targetPage.locator('a.link-external-page').filter({ hasText: 'Pubmed' })).toHaveText('Pubmed');
  });
});
