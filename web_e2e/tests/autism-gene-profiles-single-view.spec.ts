import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('Autism gene profiles single view tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToSidenavPage(page, 'autism-gene-profiles');
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('CHD8');
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();
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
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('CHD8');
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

test.describe.skip('Autism gene profiles single view dataset table tests', () => {
  let singleViewPage: Page;

  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToSidenavPage(page, 'autism-gene-profiles');
    await page.locator('input#gene-search-input').fill('GRIN2B');
    const pagePromise = context.waitForEvent('page');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
    singleViewPage = await pagePromise;
    await singleViewPage.waitForLoadState();
  });

  test('should test redirect logic', async() => {
    const page = singleViewPage;
    const queryResponse = page.waitForResponse(
      response => response.url() === utils.instanceUrl + '/api/v3/query_state/save'
    );
    const genotypeBrowserLink = page.locator('#denovo_missense > :nth-child(2) > .link-genotype-browser > span');
    await genotypeBrowserLink.click();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const queryResponseBody = await (await queryResponse).json();

    // eslint-disable-next-line max-len
    // eslint-disable-next-line @typescript-eslint/restrict-template-expressions, @typescript-eslint/no-unsafe-member-access
    await page.goto(`${utils.instanceUrl}/load-query/${queryResponseBody.uuid}`, {waitUntil: 'load'});
    await page.waitForSelector('gpf-genotype-browser');

    await expect(page.locator('label').filter({ hasText: 'missense' })).toBeChecked();
    await expect(page.locator('label').filter({ hasText: /^affected$/ })).toBeChecked();
  });
});

export const geneData = [
  {
    geneSymbols: 'GRIN2B',
    genomicScores: [
      {
        category: 'autism_scores', name: 'Autism Scores', scores: [
          { name: 'SFARI gene score', value: 1 }
        ]
      }, {
        category: 'protection_scores', name: 'Protection Scores', scores: [
          { name: 'RVIS_rank', value: 174.5 },
          { name: 'LGD_rank', value: 85.5 },
          { name: 'pLI_rank', value: 400 },
          { name: 'pRec_rank', value: 17792 }
        ]
      }
    ],
    geneSets: [
      {
        id: 'autism_gene_sets', name: 'Autism Gene Sets', scores: [
          { name: 'autism candidates from Iossifov PNAS 2015', value: true },
          { name: 'autism candidates from Sanders Neuron 2015', value: true }
        ]
      }, {
        id: 'relevant_gene_sets', name: 'Relevant Gene Sets', scores: [
          { name: 'CHD8 target genes', value: false },
          { name: 'chromatin modifiers', value: false },
          { name: 'essential genes', value: true },
          { name: 'FMRP Darnell', value: true }
        ]
      }
    ], datasets: [
      {
        name: 'iossifov_2014', columns: [
          'affected (2507)', 'unaffected (1910)'
        ], rows: [
          {
            variant_statistics: 'LGDs', variant_ids: 'denovo_lgds', affected: '3 (1.197)', unaffected: '–'
          },
          {
            variant_statistics: 'missense', variant_ids: 'denovo_missense', affected: '1 (0.399)', unaffected: '–'
          },
          {
            variant_statistics: 'intron', variant_ids: 'denovo_intron', affected: '–', unaffected: '–'
          }
        ]
      }
    ]
  }
];

test.describe('Autism gene profiles single view dynamic data tests', () => {
  let singleViewPage: Page;
  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToSidenavPage(page, 'autism-gene-profiles');
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('GRIN2B');
    const pagePromise = context.waitForEvent('page');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
    singleViewPage = await pagePromise;
    await singleViewPage.waitForLoadState();
  });

  test.skip('should compare all data in single view for GRIN2B', async() => {
    const page = singleViewPage;
    await expect(page).toHaveScreenshot('agp-single-view-GRIN2B.png', {fullPage: true});
  });
});


