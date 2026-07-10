import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { searchInGeneProfilesTable } from './utils';
import { Header } from './components/header.component';
import { GeneProfilesSingleView } from './components/gene-profiles-single-view.component';
import { GeneProfilesTable } from './components/gene-profiles-table.component';

test.describe('Gene profiles single view basic tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    const header = new Header(page);
    const geneProfilesTable = new GeneProfilesTable(page);
    await header.navLink('Gene Profiles').click();
    await searchInGeneProfilesTable(page, 'CHD8');
    await geneProfilesTable.geneCell('CHD8').click();
  });


  test('should display header', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    expect(singleView.heading).toBeTruthy();
    await expect(singleView.heading).toHaveText('CHD8');
  });

  test('should display the autism scores table', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.autismScores).toBeVisible();
    await expect(singleView.autismScores.locator('th')).toHaveText('Autism Scores');
    expect(await singleView.autismScores.locator('tr').count()).toBe(1);
  });


  test('should display the protection scores table', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.protectionScores).toBeVisible();
    await expect(singleView.protectionScores.locator('th')).toHaveText('Protection Scores');
    await expect(singleView.protectionScores.locator('tr')).toHaveCount(4);
  });


  test('should display the single scores markers', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.singleScoreMarkers).toHaveCount(5);
  });


  test('should display the autism gene sets table', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.autismGeneSets).toBeVisible();
    await expect(singleView.autismGeneSets.locator('th')).toHaveText('Autism Gene Sets');
    await expect(singleView.autismGeneSets.locator('tr')).toHaveCount(2);
  });


  test('should display the relevant gene sets table', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.relevantGeneSets).toBeVisible();
    await expect(singleView.relevantGeneSets.locator('th')).toHaveText('Relevant Gene Sets');
    await expect(singleView.relevantGeneSets.locator('tr')).toHaveCount(4);
  });

  test('should display the datasets table', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.datasetsTable).toBeVisible();
    await expect(singleView.datasetsTable.locator('th').first()).toHaveText('iossifov_2014_liftover');
    await expect(singleView.datasetsTable.locator('tr')).toHaveCount(5);
  });

  test('should display links', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.link('Gene Browser')).toBeVisible();
    await expect(singleView.link('UCSC genome browser')).toBeVisible();
    await expect(singleView.link('GeneCards')).toBeVisible();
    await expect(singleView.link('Pubmed')).toBeVisible();
    await expect(singleView.link('SFARI gene')).toBeVisible();
  });
});

test.describe('Gene profiles navigation to single view tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    const header = new Header(page);
    await header.navLink('Gene Profiles').click();

    await utils.resetGeneProfiles(page);
  });

  test('should open single view', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    const geneProfilesTable = new GeneProfilesTable(page);

    await searchInGeneProfilesTable(page, 'GRIN2B');
    await geneProfilesTable.geneCell('GRIN2B').click();

    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/GRIN2B`);
    await expect(singleView.tabsWrapper).toBeVisible();
    await expect(singleView.tab('GRIN2B')).toBeVisible();
    await expect(singleView.tab('GRIN2B')).toHaveClass('tab active-tab');
    await expect(singleView.headingFor('GRIN2B')).toBeVisible();
  });

  test('should open multiple single views, test closing and navigation', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    const geneProfilesTable = new GeneProfilesTable(page);
    await geneProfilesTable.searchInput.fill('GRIN2B');
    await geneProfilesTable.geneCell('GRIN2B').click();

    await geneProfilesTable.allGenesButton.click();
    await expect(singleView.root).not.toBeVisible();
    await expect(singleView.tableHeader).toBeVisible();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles`);

    await geneProfilesTable.geneCell('CHD8').click();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(singleView.root).toBeVisible();
    await expect(singleView.tableHeader).not.toBeVisible();

    await geneProfilesTable.allGenesButton.click();
    await expect(singleView.root).not.toBeVisible();
    await expect(singleView.tableHeader).toBeVisible();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles`);

    await expect(singleView.tabsWrapper).toContainText('GRIN2B');
    await expect(singleView.tabsWrapper).toContainText('CHD8');
    await expect(singleView.tab('GRIN2B')).toHaveClass('tab');
    await expect(singleView.tab('CHD8')).toHaveClass('tab');

    await singleView.tabsWrapper.getByText('GRIN2B').click();
    await expect(singleView.tab('GRIN2B')).toHaveClass('tab active-tab');
    await expect(singleView.root).toBeVisible();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/GRIN2B`);

    await singleView.tabsWrapper.getByText('CHD8').click();
    await expect(singleView.tab('CHD8')).toHaveClass('tab active-tab');
    await expect(singleView.tab('GRIN2B')).toHaveClass('tab');
    await expect(singleView.root).toBeVisible();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/CHD8`);

    await singleView.tabsWrapper.locator('.close-tab-button').nth(1).click();
    await expect(singleView.tableHeader).toBeVisible();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles`);
    await expect(singleView.tabsWrapper.getByText('CHD8')).not.toBeVisible();

    await singleView.tabsWrapper.locator('.close-tab-button').nth(0).click();
    await expect(singleView.tabsWrapper.getByText('GRIN2B')).not.toBeVisible();
  });

  test('should open single view of a gene multiple times', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);
    const geneProfilesTable = new GeneProfilesTable(page);

    await geneProfilesTable.geneCell('GRIN2B').click();
    await geneProfilesTable.allGenesButton.click();

    await geneProfilesTable.geneCell('GRIN2B').click();
    await expect(singleView.tabsWrapper.getByText('GRIN2B')).toHaveCount(1);
    await expect(singleView.tableHeader).not.toBeVisible();
    await expect(singleView.root).toBeVisible();
  });

  test('should open single view on new browser tab', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    const geneProfilesTable = new GeneProfilesTable(page);
    await geneProfilesTable.geneCell('CHD8').click();
    await geneProfilesTable.allGenesButton.click();

    const pagePromise = context.waitForEvent('page');
    await geneProfilesTable.geneCell('GRIN2B').click({button: 'middle'});

    const newPage = await pagePromise;
    expect(newPage.url()).toEqual(`${utils.frontendUrl}/gene-profiles/GRIN2B`);
    const singleViewNewPage = new GeneProfilesSingleView(newPage);
    await expect(singleViewNewPage.tabsWrapper.getByText('CHD8')).not.toBeVisible();
    await expect(singleViewNewPage.tab('GRIN2B')).toHaveClass('tab active-tab');
    await expect(singleViewNewPage.root).toBeVisible();

    await expect(singleView.tabsWrapper.getByText('GRIN2B')).not.toBeVisible();
    await expect(singleView.tabsWrapper.getByText('CHD8')).toBeVisible();
    await expect(singleView.tableHeader).toBeVisible();
  });

  test('should open single view when comparing genes', async({ page }) => {
    const geneProfilesTable = new GeneProfilesTable(page);

    await geneProfilesTable.rowByText('SHANK2').click({button: 'middle'});
    await geneProfilesTable.rowByText('CHD8').click({button: 'middle'});
    await expect(geneProfilesTable.compareGenesModal).toBeVisible();

    await geneProfilesTable.compareGenesCompareButton.click();

    const singleView = new GeneProfilesSingleView(page);

    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/CHD8,SHANK2`);
    await expect(singleView.root).toHaveCount(2);

    await expect(singleView.tabsWrapper.getByText('CHD8,SHANK2')).toBeVisible();
    await expect(singleView.tab('CHD8,SHANK2')).toHaveClass('tab active-tab');
  });

  test('should open single view and check table\'s state', async({ page }) => {
    const geneProfilesTable = new GeneProfilesTable(page);
    await searchInGeneProfilesTable(page, 'GRIN2B');

    await expect(geneProfilesTable.dataRows).toContainText('GRIN2B');
    await geneProfilesTable.geneCell('GRIN2B').click();

    await geneProfilesTable.allGenesButton.click();
    await expect(geneProfilesTable.searchInput).toHaveValue('GRIN2B');
    await geneProfilesTable.searchClearIcon.click();

    await geneProfilesTable.categoryFilteringButton.click();
    await geneProfilesTable.menuOption('Relevant Gene Sets').click();
    await geneProfilesTable.rowByText('SHANK2').click({button: 'middle'});
    await geneProfilesTable.rowByText('CHD8').click({button: 'middle'});

    const singleView = new GeneProfilesSingleView(page);

    await singleView.tabsWrapper.getByText('GRIN2B').click();
    await geneProfilesTable.allGenesButton.click();

    await expect(page.getByTitle('Relevant Gene Sets')).not.toBeVisible();
    await expect(geneProfilesTable.rowByText('SHANK2')).toHaveClass(/row-highlight/);
    await expect(geneProfilesTable.rowByText('CHD8')).toHaveClass(/row-highlight/);
  });

  test('should open single view for the same genes when comparing', async({ page }) => {
    const geneProfilesTable = new GeneProfilesTable(page);
    await geneProfilesTable.rowByText('SHANK2').click({button: 'middle'});
    await geneProfilesTable.rowByText('CHD8').click({button: 'middle'});

    await geneProfilesTable.compareGenesCompareButton.click();
    await geneProfilesTable.allGenesButton.click();

    await geneProfilesTable.compareGenesCompareButton.click();
    expect(page.url()).toEqual(`${utils.frontendUrl}/gene-profiles/CHD8,SHANK2`);

    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.tabsWrapper.getByText('CHD8,SHANK2')).toHaveCount(1);
    await expect(singleView.tab('CHD8,SHANK2')).toHaveClass('tab active-tab');
  });


  test('should navigate to single view with url', async({ page }) => {
    await page.goto(`${utils.frontendUrl}/gene-profiles/CHD8`);

    const singleView = new GeneProfilesSingleView(page);
    await expect(singleView.tabsWrapper.getByRole('button', { name: 'CHD8 close' })).toBeVisible();
    await expect(singleView.tableHeader).not.toBeVisible();
    await expect(singleView.root).toBeVisible();
    await expect(singleView.headingFor('CHD8')).toBeVisible();
  });

  test('should navigate to single view with invalid gene', async({ page }) => {
    const geneProfilesTable = new GeneProfilesTable(page);
    const singleView = new GeneProfilesSingleView(page);
    await page.goto(`${utils.frontendUrl}/gene-profiles/CHD8`);
    await expect(singleView.headingFor('CHD8')).toBeVisible();

    await page.goto(`${utils.frontendUrl}/gene-profiles/CHD888`);

    await expect(singleView.root).not.toBeVisible();
    await page.waitForSelector('.error-modal');
    await expect(singleView.errorModal).toContainText('CHD888" is not found in the gene profiles database!');

    await singleView.errorModal.getByText('Back').click();
    await expect(singleView.errorModal).not.toBeVisible();
    await expect(geneProfilesTable.root).toBeVisible();
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
        name: 'iossifov_2014_liftover', columns: [
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
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    const header = new Header(page);
    const geneProfilesTable = new GeneProfilesTable(page);
    await header.navLink('Gene Profiles').click();

    await utils.resetGeneProfiles(page);

    await searchInGeneProfilesTable(page, 'GRIN2B');
    await geneProfilesTable.geneCell('GRIN2B').click();
    await page.waitForSelector('gpf-gene-profiles-single-view');
  });

  test('should compare all data in single view for GRIN2B', async({ page }) => {
    const singleView = new GeneProfilesSingleView(page);

    await expect(singleView.autismGeneSets.locator('th')).toHaveText('Autism Gene Sets');
    await expect(
      singleView.geneSetsTable.locator('tr').nth(0)
    ).toHaveText('autism candidates from Iossifov PNAS 2015check');
    await expect(
      singleView.geneSetsTable.locator('tr').nth(1)
    ).toHaveText('autism candidates from Sanders Neuron 2015check');


    await expect(singleView.datasetsTable.locator('th').nth(0)).toHaveText('iossifov_2014_liftover');
    await expect(
      singleView.datasetsTable.locator('tr').nth(1)
    ).toHaveText('Variant Statisticsaffected (2507)unaffected (1910)');
    await expect(singleView.datasetsTable.locator('tr').nth(2)).toHaveText('LGDsremoveremove');
    await expect(singleView.datasetsTable.locator('tr').nth(3)).toHaveText('missenseremoveremove');
    await expect(singleView.datasetsTable.locator('tr').nth(4)).toHaveText('intronremoveremove');

    await expect(singleView.relevantGeneSets.locator('th')).toHaveText('Relevant Gene Sets');
    await expect(singleView.relevantGeneSets.locator('tr').nth(0)).toHaveText('CHD8 target genes');
    await expect(singleView.relevantGeneSets.locator('tr').nth(1)).toHaveText('chromatin modifiers');
    await expect(singleView.relevantGeneSets.locator('tr').nth(2)).toHaveText('essential genescheck');
    await expect(singleView.relevantGeneSets.locator('tr').nth(3)).toHaveText('FMRP Darnellcheck');
  });

  test('should navigate to Gene Browser from single view', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    const pagePromise = context.waitForEvent('page');

    await singleView.link('Gene Browser').click();

    const newPage = await pagePromise;
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('/gene-browser/GRIN2B');
  });

  test('should navigate to UCSC genome browser from single view', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    await singleView.link('UCSC genome browser').click();

    const newPage = await context.waitForEvent('page');
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://genome.ucsc.edu/');
  });

  test('should navigate to GeneCards from single view', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    await singleView.link('GeneCards').click();

    const newPage = await context.waitForEvent('page');
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://www.genecards.org/');
  });

  test('should navigate to Pubmed from single view', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    await singleView.link('Pubmed').click();

    const newPage = await context.waitForEvent('page');
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('pubmed.ncbi.nlm.nih.gov/');
  });

  test('should navigate to SFARI gene from single view', async({ page, context }) => {
    const singleView = new GeneProfilesSingleView(page);
    await singleView.link('SFARI gene').click();

    const newPage = await context.waitForEvent('page');
    await newPage.waitForLoadState();

    expect(newPage.url()).toContain('https://gene.sfari.org/');
  });
});
