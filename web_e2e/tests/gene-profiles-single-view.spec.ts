import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Gene profiles single view basic tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('CHD8');
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();
  });


  test('should display header', async({ page }) => {
    expect(page.locator('gpf-gene-profiles-single-view h2')).toBeTruthy();
    await expect(page.locator('gpf-gene-profiles-single-view h2')).toHaveText('CHD8');
  });

  test('should display the autism scores table', async({ page }) => {
    await expect(page.locator('#autism_scores')).toBeVisible();
    await expect(page.locator('#autism_scores th')).toHaveText('Autism Scores');
    expect(await page.locator('#autism_scores tr').count()).toBe(1);
  });


  test('should display the protection scores table', async({ page }) => {
    await expect(page.locator('#protection_scores')).toBeVisible();
    await expect(page.locator('#protection_scores th')).toHaveText('Protection Scores');
    await expect(page.locator('#protection_scores tr')).toHaveCount(4);
  });


  test('should display the single scores markers', async({ page }) => {
    await expect(page.locator('.single-score-marker')).toHaveCount(5);
  });


  test('should display the autism gene sets table', async({ page }) => {
    await expect(page.locator('#autism_gene_sets')).toBeVisible();
    await expect(page.locator('#autism_gene_sets th')).toHaveText('Autism Gene Sets');
    await expect(page.locator('#autism_gene_sets tr')).toHaveCount(2);
  });


  test('should display the relevant gene sets table', async({ page }) => {
    await expect(page.locator('#relevant_gene_sets')).toBeVisible();
    await expect(page.locator('#relevant_gene_sets th')).toHaveText('Relevant Gene Sets');
    await expect(page.locator('#relevant_gene_sets tr')).toHaveCount(4);
  });

  test('should display the datasets table', async({ page }) => {
    await expect(page.locator('.datasets-table')).toBeVisible();
    await expect(page.locator('.datasets-table th').first()).toHaveText('iossifov_2014');
    await expect(page.locator('.datasets-table tr')).toHaveCount(5);
  });

  test('should display links', async({ page }) => {
    await expect(page.getByRole('link', { name: 'Gene Browser' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'UCSC genome browser' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'GeneCards' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Pubmed' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'SFARI gene' })).toBeVisible();
  });
});

test.describe('Gene profiles navigation to single view tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await page.locator('#header a:text("Gene Profiles")').click();
  });

  test('should open single view', async({ page }) => {
    await page.locator('input#gene-search-input').fill('GRIN2B');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();

    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/GRIN2B`);
    await expect(page.locator('#tabs-wrapper')).toBeVisible();
    await expect(page.getByRole('button', {name: 'GRIN2B'})).toBeVisible();
    await expect(page.getByRole('button', {name: 'GRIN2B'})).toHaveClass('tab active-tab');
    await expect(page.locator('gpf-gene-profiles-single-view').locator('h2:text("GRIN2B")')).toBeVisible();
  });

  test('should open multiple single views, test closing and navigation', async({ page }) => {
    await page.locator('input#gene-search-input').fill('GRIN2B');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();

    await page.getByRole('button', {name: 'All genes'}).click();
    await expect(page.locator('gpf-gene-profiles-single-view')).not.toBeVisible();
    await expect(page.locator('#table-header')).toBeVisible();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles`);

    await page.locator('div').filter({ hasText: /^CHD8$/}).click();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/CHD8`);
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    await expect(page.locator('#table-header')).not.toBeVisible();

    await page.getByRole('button', {name: 'All genes'}).click();
    await expect(page.locator('gpf-gene-profiles-single-view')).not.toBeVisible();
    await expect(page.locator('#table-header')).toBeVisible();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles`);

    await expect(page.locator('#tabs-wrapper')).toContainText('GRIN2B');
    await expect(page.locator('#tabs-wrapper')).toContainText('CHD8');
    await expect(page.getByRole('button', {name: 'GRIN2B'})).toHaveClass('tab');
    await expect(page.getByRole('button', {name: 'CHD8'})).toHaveClass('tab');

    await page.locator('#tabs-wrapper').getByText('GRIN2B').click();
    await expect(page.getByRole('button', {name: 'GRIN2B'})).toHaveClass('tab active-tab');
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/GRIN2B`);

    await page.locator('#tabs-wrapper').getByText('CHD8').click();
    await expect(page.getByRole('button', {name: 'CHD8'})).toHaveClass('tab active-tab');
    await expect(page.getByRole('button', {name: 'GRIN2B'})).toHaveClass('tab');
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/CHD8`);

    await page.locator('#tabs-wrapper').locator('.close-tab-button').nth(1).click();
    await expect(page.locator('#table-header')).toBeVisible();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles`);
    await expect(page.locator('#tabs-wrapper').getByText('CHD8')).not.toBeVisible();

    await page.locator('#tabs-wrapper').locator('.close-tab-button').nth(0).click();
    await expect(page.locator('#tabs-wrapper').getByText('GRIN2B')).not.toBeVisible();
  });

  test('should open single view of a gene multiple times', async({ page }) => {
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
    await page.getByRole('button', {name: 'All genes'}).click();

    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
    await expect(page.locator('#tabs-wrapper').getByText('GRIN2B')).toHaveCount(1);
    await expect(page.locator('#table-header')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
  });

  test('should open single view on new browser tab', async({ page, context }) => {
    await page.locator('div').filter({ hasText: /^CHD8$/}).click();
    await page.getByRole('button', {name: 'All genes'}).click();

    const pagePromise = context.waitForEvent('page');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click({button: 'middle'});

    const newPage = await pagePromise;
    expect(newPage.url()).toEqual(`${utils.instanceUrl}/gene-profiles/GRIN2B`);
    await expect(newPage.locator('#tabs-wrapper').getByText('CHD8')).not.toBeVisible();
    await expect(newPage.getByRole('button', {name: 'GRIN2B'})).toHaveClass('tab active-tab');
    await expect(newPage.locator('gpf-gene-profiles-single-view').locator('h2:text("GRIN2B")')).toBeVisible();

    await expect(page.locator('#tabs-wrapper').getByText('GRIN2B')).not.toBeVisible();
    await expect(page.locator('#tabs-wrapper').getByText('CHD8')).toBeVisible();
    await expect(page.locator('#table-header')).toBeVisible();
  });

  test('should open single view when comparing genes', async({ page }) => {
    await page.locator('.table-body-row').filter({ hasText: 'SHANK2' }).click({button: 'middle'});
    await page.locator('.table-body-row').filter({ hasText: 'CHD8' }).click({button: 'middle'});
    await expect(page.locator('#compare-genes-modal')).toBeVisible();

    await page.locator('#compare-genes-compare-button').click();

    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/CHD8,SHANK2`);
    await expect(page.locator('gpf-gene-profiles-single-view')).toHaveCount(2);

    await expect(page.locator('#tabs-wrapper').getByText('CHD8,SHANK2')).toBeVisible();
    await expect(page.getByRole('button', {name: 'CHD8,SHANK2'})).toHaveClass('tab active-tab');
  });

  test('should open single view and check table\'s state', async({ page }) => {
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('GRIN2B');
    await page.waitForTimeout(500);

    await expect(page.locator('.table-body-row').filter({hasNotText: 'Nothing found'})).toContainText('GRIN2B');
    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();

    await page.getByRole('button', {name: 'All genes'}).click();
    await expect(page.locator('input#gene-search-input')).toHaveValue('GRIN2B');
    await page.locator('.search-clear-icon').click();

    await page.locator('#category-filtering-button').click();
    await page.getByLabel('Relevant Gene Sets').click();
    await page.locator('.table-body-row').filter({ hasText: 'SHANK2' }).click({button: 'middle'});
    await page.locator('.table-body-row').filter({ hasText: 'CHD8' }).click({button: 'middle'});

    await page.locator('#tabs-wrapper').getByText('GRIN2B').click();
    await page.getByRole('button', {name: 'All genes'}).click();

    await expect(page.getByTitle('Relevant Gene Sets')).not.toBeVisible();
    await expect(page.locator('.table-body-row').filter({ hasText: 'SHANK2' }))
      .toHaveClass(/row-highlight/);
    await expect(page.locator('.table-body-row').filter({ hasText: 'CHD8' }))
      .toHaveClass(/row-highlight/);
  });

  test('should open single view for the same genes when comparing', async({ page }) => {
    await page.locator('.table-body-row').filter({ hasText: 'SHANK2' }).click({button: 'middle'});
    await page.locator('.table-body-row').filter({ hasText: 'CHD8' }).click({button: 'middle'});

    await page.locator('#compare-genes-compare-button').click();

    await page.getByRole('button', {name: 'All genes'}).click();

    await page.locator('#compare-genes-compare-button').click();
    expect(page.url()).toEqual(`${utils.instanceUrl}/gene-profiles/CHD8,SHANK2`);

    await expect(page.locator('#tabs-wrapper').getByText('CHD8,SHANK2')).toHaveCount(1);
    await expect(page.getByRole('button', {name: 'CHD8,SHANK2'})).toHaveClass('tab active-tab');
  });


  test('should navigate to single view with url', async({ page }) => {
    await page.goto(`${utils.instanceUrl}/gene-profiles/CHD8`);

    await expect(page.locator('#tabs-wrapper').getByText('CHD8')).toBeVisible();
    await expect(page.locator('#table-header')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-single-view')).toBeVisible();
    await expect(page.locator('gpf-gene-profiles-single-view').locator('h2:text("CHD8")')).toBeVisible();
  });

  test('should navigate to single view with invalid gene', async({ page }) => {
    await page.goto(`${utils.instanceUrl}/gene-profiles/CHD8`);
    await expect(page.getByRole('heading', {name: 'CHD8'})).toBeVisible();

    await page.goto(`${utils.instanceUrl}/gene-profiles/CHD888`);
    await expect(page.locator('gpf-gene-profiles-single-view')).not.toBeVisible();
    await page.waitForSelector('.error-modal');
    await expect(page.locator('.error-modal')).toContainText('CHD888" is not found in the gene profiles database!');

    await page.locator('.error-modal').getByText('Back').click();
    await expect(page.locator('.error-modal')).not.toBeVisible();
    await expect(page.locator('gpf-gene-profiles-table')).toBeVisible();
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

test.describe('Gene profiles single view dynamic data and links tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await page.locator('#header a:text("Gene Profiles")').click();
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('GRIN2B');
    await page.waitForLoadState();

    await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
  });

  test('should compare all data in single view for GRIN2B', async({ page }) => {
    await expect(page.locator('#autism_gene_sets').locator('th')).toHaveText('Autism Gene Sets');
    await expect(
      page.locator('.gene-sets-table').locator('tr').nth(0)
    ).toHaveText('autism candidates from Iossifov PNAS 2015check');
    await expect(
      page.locator('.gene-sets-table').locator('tr').nth(1)
    ).toHaveText('autism candidates from Sanders Neuron 2015check');


    await expect(page.locator('.datasets-table').locator('th').nth(0)).toHaveText('iossifov_2014');
    await expect(
      page.locator('.datasets-table').locator('tr').nth(1)
    ).toHaveText('Variant Statisticsaffected (2507)unaffected (1910)');
    await expect(page.locator('.datasets-table').locator('tr').nth(2)).toHaveText('LGDs3 (1.197)remove');
    await expect(page.locator('.datasets-table').locator('tr').nth(3)).toHaveText('missense1 (0.399)remove');
    await expect(page.locator('.datasets-table').locator('tr').nth(4)).toHaveText('intronremoveremove');

    await expect(page.locator('#relevant_gene_sets').locator('th')).toHaveText('Relevant Gene Sets');
    await expect(page.locator('#relevant_gene_sets').locator('tr').nth(0)).toHaveText('CHD8 target genes');
    await expect(page.locator('#relevant_gene_sets').locator('tr').nth(1)).toHaveText('chromatin modifiers');
    await expect(page.locator('#relevant_gene_sets').locator('tr').nth(2)).toHaveText('essential genescheck');
    await expect(page.locator('#relevant_gene_sets').locator('tr').nth(3)).toHaveText('FMRP Darnellcheck');
  });

  test('should navigate to Gene Browser from single view', async({ page, context }) => {
    const pagePromise = context.waitForEvent('page');

    await page.getByRole('link', { name: 'Gene Browser' }).click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('/gene-browser/GRIN2B');
  });

  test('should navigate to UCSC genome browser from single view', async({ page, context }) => {
    const pagePromise = context.waitForEvent('page');

    await page.getByRole('link', { name: 'UCSC genome browser' }).click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://genome.ucsc.edu/');
  });

  test('should navigate to GeneCards from single view', async({ page, context }) => {
    const pagePromise = context.waitForEvent('page');

    await page.getByRole('link', { name: 'GeneCards' }).click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://www.genecards.org/');
  });

  test('should navigate to Pubmed from single view', async({ page, context }) => {
    const pagePromise = context.waitForEvent('page');

    await page.getByRole('link', { name: 'Pubmed' }).click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('pubmed.ncbi.nlm.nih.gov/');
  });

  test('should navigate to SFARI gene from single view', async({ page, context }) => {
    const pagePromise = context.waitForEvent('page');

    await page.getByRole('link', { name: 'SFARI gene' }).click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://gene.sfari.org/');
  });
});

