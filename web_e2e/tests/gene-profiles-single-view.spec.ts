import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('Gene profiles single view tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('CHD8');
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();
  });


  test('should display header', async({ context }) => {
    const targetPage = context.pages()[1];
    expect(targetPage.locator('gpf-gene-profiles-single-view h2')).toBeTruthy();
    await expect(targetPage.locator('gpf-gene-profiles-single-view h2')).toHaveText('CHD8');
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

test.describe('Gene profiles single view links tests', () => {
  let CHD8Page: Page;
  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
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
    await expect(targetPage.getByText('UCSC genome browser')).toBeVisible();
  });

  test('should display GeneCards link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.getByText('GeneCards')).toBeVisible();
  });

  test('should display Pubmed link', async({ context }) => {
    const targetPage = context.pages()[1];
    await expect(targetPage.getByText('Pubmed')).toBeVisible();
  });
});

test.describe.skip('Gene profiles single view dataset table tests', () => {
  let singleViewPage: Page;

  test.beforeEach(async({ page, context }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await page.locator('#header a:text("Gene Profiles")').click();
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

export const geneData =
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
  };

test.describe('Gene profiles single view dynamic data tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await page.locator('#header a:text("Gene Profiles")').click();
  });

  test('should compare all data in single view for GRIN2B', async({ page, context }) => {
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('GRIN2B');
    await page.waitForLoadState();

    const pr = context.waitForEvent('page');

    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
    const singleViewPage = await pr;

    await expect(singleViewPage.locator('#autism_gene_sets').locator('th')).toHaveText('Autism Gene Sets');
    await expect(
      singleViewPage.locator('.gene-sets-table').locator('tr').nth(0)
    ).toHaveText('autism candidates from Iossifov PNAS 2015check');
    await expect(
      singleViewPage.locator('.gene-sets-table').locator('tr').nth(1)
    ).toHaveText('autism candidates from Sanders Neuron 2015check');


    await expect(singleViewPage.locator('.datasets-table').locator('th').nth(0)).toHaveText('iossifov_2014');
    await expect(
      singleViewPage.locator('.datasets-table').locator('tr').nth(1)
    ).toHaveText('Variant Statisticsaffected (2507)unaffected (1910)');
    await expect(singleViewPage.locator('.datasets-table').locator('tr').nth(2)).toHaveText('LGDs3 (1.197)remove');
    await expect(singleViewPage.locator('.datasets-table').locator('tr').nth(3)).toHaveText('missense1 (0.399)remove');
    await expect(singleViewPage.locator('.datasets-table').locator('tr').nth(4)).toHaveText('intronremoveremove');

    await expect(singleViewPage.locator('#relevant_gene_sets').locator('th')).toHaveText('Relevant Gene Sets');
    await expect(singleViewPage.locator('#relevant_gene_sets').locator('tr').nth(0)).toHaveText('CHD8 target genes');
    await expect(singleViewPage.locator('#relevant_gene_sets').locator('tr').nth(1)).toHaveText('chromatin modifiers');
    await expect(singleViewPage.locator('#relevant_gene_sets').locator('tr').nth(2)).toHaveText('essential genescheck');
    await expect(singleViewPage.locator('#relevant_gene_sets').locator('tr').nth(3)).toHaveText('FMRP Darnellcheck');
  });
});


