import { test, expect, Page, Response } from '@playwright/test';
import * as utils from './utils';
import { searchInGeneProfilesTable } from './utils';

interface GeneProfilesState {
  openedTabs: string[];
  searchValue: string;
  highlightedRows: string[];
  sortBy: string;
  orderBy: string;
  headerLeaves: string[];
}

test.describe('Gene profiles row data tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });

  [
    {
      geneSymbol: 'CHD8',
      // eslint-disable-next-line max-len
      expectedRow: ['CHD8', 'check_small', 'check_small', '', 'check_small', 'check_small', 'check_small', '1', '193', '83', '31.5', '18178', '7.0 (2.79)', '', '', '', '', '']
    },
    {
      geneSymbol: 'SHANK2',
      // eslint-disable-next-line max-len
      expectedRow: ['SHANK2', 'check_small', 'check_small', '', '', '', 'check_small', '1', '', '43', '649', '17517', '', '', '', '', '', '']
    },
    {
      geneSymbol: 'FLG',
      // eslint-disable-next-line max-len
      expectedRow: ['FLG', '', '', '', '', 'check_small', '', '', '16640', '18394.5', '', '', '1.0 (0.4)', '', '', '', '', '']
    },
    {
      geneSymbol: 'CMIP',
      // eslint-disable-next-line max-len
      expectedRow: ['CMIP', '', '', 'check_small', '', '', '', '3', '558', '2494', '694', '17467', '', '', '', '', '', '']
    },
    {
      geneSymbol: 'TBCD',
      // eslint-disable-next-line max-len
      expectedRow: ['TBCD', '', '', 'check_small', '', '', '', '', '646', '9111.5', '13275.5', '222', '', '', '', '', '', '']
    }
  ].forEach(data => {
    test(`should display correct gene data for ${data.geneSymbol}`, async({ page }) => {
      await searchInGeneProfilesTable(page, data.geneSymbol);
      await expect(page.locator('.table-body-row:not(#nothing-found)')).toHaveCount(1);

      const cells = await page.locator('.table-body-row').locator('.row-cell').all();
      await Promise.all(cells.map(async(cell, i) => {
        await expect(cell).toHaveText(data.expectedRow[i]);
        i++;
      }));
    });
  });
});

test.describe('Gene profiles table column filtering tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });

  test('should open autism gene sets dropdown after clicking on' +
  ' the autism gene sets columns filtering button', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();
    await expect(page.locator('gpf-multiple-select-menu')).toBeVisible();
    await expect(page.locator('gpf-multiple-select-menu #check-uncheck-all-button')).toBeVisible();
    await expect(page.locator('gpf-multiple-select-menu input[name="search"]')).toBeVisible();
  });

  test('should check/uncheck all gene sets column filtering options' +
  ' using the check/uncheck all button', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();
    await expect(page.locator('gpf-multiple-select-menu')
      .getByLabel('autism candidates from Iossifov PNAS 2015')).toBeChecked();
    await expect(page.locator('gpf-multiple-select-menu')
      .getByLabel('autism candidates from Sanders Neuron 2015')).toBeChecked();

    await page.locator('gpf-multiple-select-menu #check-uncheck-all-button').click();
    await expect(page.locator('gpf-multiple-select-menu')
      .getByLabel('autism candidates from Iossifov PNAS 2015')).not.toBeChecked();
    await expect(page.locator('gpf-multiple-select-menu')
      .getByLabel('autism candidates from Sanders Neuron 2015')).not.toBeChecked();
  });

  test('should change the check/uncheck button text', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();
    await expect(page.locator('gpf-multiple-select-menu #check-uncheck-all-button')).toHaveText('Uncheck all');

    await page.locator('gpf-multiple-select-menu #check-uncheck-all-button').click();
    await expect(page.locator('gpf-multiple-select-menu #check-uncheck-all-button')).toHaveText('Check all');

    await page.locator('gpf-multiple-select-menu #check-uncheck-all-button').click();
    await expect(page.locator('gpf-multiple-select-menu #check-uncheck-all-button')).toHaveText('Uncheck all');
  });

  test('should hide columns using the check/uncheck button', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();
    await page.locator('gpf-multiple-select-menu #check-uncheck-all-button').click();

    await expect(page.locator('.header-cell').filter({hasText: 'Autism Gene Sets'})).not.toBeVisible();
    await expect(
      page.locator('.header-cell').filter({hasText: 'autism candidates from Iossifov PNAS 2015'})
    ).not.toBeVisible();

    await expect(
      page.locator('.header-cell').filter({hasText: 'autism candidates from Sanders Neuron 2015'})
    ).not.toBeVisible();

    await page.mouse.click(0, 0);
    await page.locator('#category-filtering-button').click();
    await expect(page.locator('gpf-multiple-select-menu').getByLabel('Autism Gene Sets')).not.toBeChecked();

    await page.locator('gpf-multiple-select-menu').getByLabel('Autism Gene Sets').click();
    await page.mouse.click(0, 0);
    await expect(page.locator('.header-cell').filter({hasText: 'Autism Gene Sets'})).toBeVisible();
    await expect(
      page.locator('.header-cell').filter({hasText: 'autism candidates from Iossifov PNAS 2015'})
    ).toBeVisible();

    await expect(
      page.locator('.header-cell').filter({hasText: 'autism candidates from Sanders Neuron 2015'})
    ).toBeVisible();
  });

  test('should filter gene sets dropdown options using the search', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();
    await expect(page.locator('gpf-multiple-select-menu label')).toHaveCount(2);

    await page.locator('gpf-multiple-select-menu input[name="search"]').fill('iossifov');
    await expect(page.locator('gpf-multiple-select-menu label')).toHaveCount(1);
  });

  test('should uncheck gene set from autism gene sets dropdown and check table header', async({ page }) => {
    await page.locator('#autism_gene_sets_rank-column-filtering-button').click();

    await page.locator('gpf-multiple-select-menu label')
      .getByLabel('autism candidates from Sanders Neuron 2015').click();

    await expect(page.getByTitle('autism candidates from Sanders Neuron 2015')).not.toBeVisible();

    await page.locator('gpf-multiple-select-menu label')
      .getByLabel('autism candidates from Sanders Neuron 2015').click();

    await expect(page.getByTitle('autism candidates from Sanders Neuron 2015')).toBeVisible();
  });

  test('should uncheck iossifov_2014 and check table header', async({ page }) => {
    const headerCell = page.locator('.header-cell');
    await page.locator('#category-filtering-button').click();
    await page.locator('gpf-multiple-select-menu').getByLabel('iossifov_2014_liftover').click();
    await expect(headerCell.getByText('iossifov_2014_liftover', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('affected (2507)', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('unaffected (1910)', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell).toHaveCount(16);

    await page.locator('gpf-multiple-select-menu').getByLabel('iossifov_2014_liftover').click();
    await expect(headerCell.getByText('iossifov_2014_liftover', { exact: true})).toBeVisible();
    await expect(headerCell.getByText('affected (2507)', { exact: true})).toBeVisible();
    await expect(headerCell.getByText('unaffected (1910)', { exact: true})).toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(0)).toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(1)).toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(0)).toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(1)).toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(0)).toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(1)).toBeVisible();
    await expect(headerCell).toHaveCount(25);
  });

  test('should drag and drop gene set and check table header', async({ page }) => {
    await page.locator('#category-filtering-button').click();
    const columnHeader = page.locator('.header-cell-content-span');
    await expect(page.locator('gpf-multiple-select-menu label').nth(0)).toHaveText('Autism Gene Sets');
    await expect(columnHeader.nth(1)).toHaveText('Autism Gene Sets');
    await expect(columnHeader.nth(2)).toHaveText('autism candidates from Iossifov PNAS 2015');
    await expect(columnHeader.nth(3)).toHaveText('autism candidates from Sanders Neuron 2015');

    await page.locator('gpf-multiple-select-menu label').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(530, 300, {steps: 2});
    await page.mouse.up();

    await expect(page.locator('gpf-multiple-select-menu label').nth(0)).toHaveText('Relevant Gene Sets');
    await expect(page.locator('gpf-multiple-select-menu label').nth(1)).toHaveText('Autism Gene Sets');

    await expect(columnHeader.nth(1)).toHaveText('Relevant Gene Sets');
    await expect(columnHeader.nth(2)).toHaveText('CHD8 target genes');
    await expect(columnHeader.nth(3)).toHaveText('chromatin modifiers');
    await expect(columnHeader.nth(4)).toHaveText('essential genes');
    await expect(columnHeader.nth(5)).toHaveText('FMRP Darnell');

    await expect(columnHeader.nth(6)).toHaveText('Autism Gene Sets');
    await expect(columnHeader.nth(7)).toHaveText('autism candidates from Iossifov PNAS 2015');
    await expect(columnHeader.nth(8)).toHaveText('autism candidates from Sanders Neuron 2015');
  });
});

test.describe('Gene profiles gene comparison tests', () => {
  const oddHighlightColor = 'rgb(247, 247, 203)';
  const evenHighlightColor = 'rgb(255, 255, 214)';
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });
  test('should highlight a row using control+click and change it\'s background color', async({ page }) => {
    const firstRow = page.locator('.table-body-row:not(#nothing-found)').nth(0);
    await expect(firstRow).not.toHaveClass(/row-highlight/);

    await page.keyboard.down('Control');
    await firstRow.click();

    // hover another row to check the background color
    await page.locator('.table-body-row:not(#nothing-found)').nth(1).hover();
    await expect(firstRow).toHaveClass(/row-highlight/);
    await expect(firstRow).toHaveCSS('background-color', oddHighlightColor);

    await page.keyboard.down('Control');
    await firstRow.click();

    // hover another row to check the background color
    await page.locator('.table-body-row:not(#nothing-found)').nth(1).hover();
    await expect(firstRow).not.toHaveClass(/row-highlight/);
    await expect(firstRow).not.toHaveCSS('background-color', oddHighlightColor);
  });

  test('should highlight a several rows and check whether ' +
    'background color is different for odd and even rows', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.keyboard.down('Control');
    await row.nth(0).click();
    await row.nth(1).click();
    await row.nth(2).click();
    await row.nth(3).click();
    await row.nth(4).click();

    // hover another row to check the background color
    await row.nth(6).hover();
    await expect(row.nth(0)).toHaveCSS('background-color', oddHighlightColor);
    await expect(row.nth(1)).toHaveCSS('background-color', evenHighlightColor);
    await expect(row.nth(2)).toHaveCSS('background-color', oddHighlightColor);
    await expect(row.nth(3)).toHaveCSS('background-color', evenHighlightColor);
    await expect(row.nth(4)).toHaveCSS('background-color', oddHighlightColor);
  });

  test('should highlight the first 3 rows and then press escape to remove all highlights', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.keyboard.down('Control');
    await row.nth(0).click();
    await row.nth(1).click();
    await row.nth(2).click();

    await expect(row.nth(0)).toHaveClass(/row-highlight/);
    await expect(row.nth(1)).toHaveClass(/row-highlight/);
    await expect(row.nth(2)).toHaveClass(/row-highlight/);
    await page.keyboard.up('Control');

    await page.keyboard.press('Escape');
    await expect(row.nth(0)).not.toHaveClass(/row-highlight/);
    await expect(row.nth(1)).not.toHaveClass(/row-highlight/);
    await expect(row.nth(2)).not.toHaveClass(/row-highlight/);
  });

  test('should select multiple genes and check whether the modal appears correctly', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.keyboard.down('Control');
    await row.nth(0).click();
    await row.nth(1).click();
    await row.nth(2).click();

    await expect(page.locator('#compare-genes-modal')).toBeVisible();
    await expect(page.locator('.compare-gene-item')).toHaveCount(3);

    await page.keyboard.down('Control');
    await row.nth(0).click();
    await row.nth(1).click();
    await row.nth(2).click();

    await expect(page.locator('#compare-genes-modal')).not.toBeVisible();
  });

  test('should select multiple genes and remove them from modal', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.keyboard.down('Control');
    await row.nth(0).click();
    await row.nth(1).click();
    await row.nth(2).click();

    await page.locator('.compare-genes-close').nth(0).click();
    await expect(row.nth(0)).not.toHaveClass(/row-highlight/);
    await expect(page.locator('.compare-gene-item')).toHaveCount(2);

    await page.locator('.compare-genes-close').nth(0).click();
    await expect(row.nth(1)).not.toHaveClass(/row-highlight/);
    await expect(page.locator('.compare-gene-item')).toHaveCount(1);

    await page.locator('.compare-genes-close').nth(0).click();
    await expect(row.nth(2)).not.toHaveClass(/row-highlight/);
    await expect(page.locator('.compare-genes-close')).not.toBeVisible();
  });
});

test.describe('Gene profiles table functionality tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await page.locator('#header a:text("Gene Profiles")').click();
    await page.waitForSelector('gpf-gene-profiles-table');
    await page.waitForSelector('#loading', {state: 'detached'});

    await utils.resetGeneProfiles(page);
  });
  test('should sort genes by autism gene sets', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await searchInGeneProfilesTable(page, 'RAPGEF');
    await expect(row).toHaveCount(4);

    await page.locator('#category-filtering-button').click();
    await page.locator('#check-uncheck-all-button').click();
    await page.getByLabel('Autism Gene Sets').click();
    await page.locator('#category-filtering-button').click();

    await expect(row.nth(0).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(0).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(1).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(1).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(2).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(2).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(3).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(3).locator('.row-cell').nth(2)).toHaveText('');

    await page.locator('.header-cell').getByText('Autism Gene Sets').click();
    await page.waitForTimeout(200);
    await expect(row.nth(0).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(0).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(1).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(1).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(2).locator('.row-cell').nth(1)).toHaveText('');
    await expect(row.nth(2).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(3).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(3).locator('.row-cell').nth(2)).toHaveText('');
  });

  test('should sort genes by relevant gene sets', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await searchInGeneProfilesTable(page, 'SENP');
    await expect(page.locator('.search-loading-icon')).toHaveCount(0);
    await expect(row).toHaveCount(6);

    await page.locator('#category-filtering-button').click();
    await page.locator('#check-uncheck-all-button').click();
    await page.getByLabel('Relevant Gene Sets').click();
    await page.locator('#category-filtering-button').click();

    await page.locator('.header-cell').getByText('Relevant Gene Sets').click();
    await page.waitForTimeout(200);

    await expect(row.nth(0).getByText('check_small')).toHaveCount(2);
    await expect(row.nth(1).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(2).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(3).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(4).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(5).getByText('check_small')).toHaveCount(1);

    await page.locator('.header-cell').getByText('Relevant Gene Sets').click();
    await page.waitForTimeout(200);

    await expect(row.nth(0).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(1).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(2).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(3).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(4).getByText('check_small')).toHaveCount(1);
    await expect(row.nth(5).getByText('check_small')).toHaveCount(2);
  });

  test('should test the values in SFARI gene score column', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');

    await expect(row).toHaveCount(16);
    await expect(row.nth(0).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(1).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(2).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(3).locator('.row-cell').nth(7)).toHaveText('3');

    await page.getByText('SFARI gene score').click();
    await page.waitForTimeout(500);
    await expect(row.nth(0).locator('.row-cell').nth(7)).toHaveText('3');
    await expect(row.nth(1).locator('.row-cell').nth(7)).toHaveText('3');
    await expect(row.nth(2).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(3).locator('.row-cell').nth(7)).toHaveText('1');

    await page.getByText('SFARI gene score').click();
    await page.waitForTimeout(500);
    await expect(row.nth(0).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(1).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(2).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(3).locator('.row-cell').nth(7)).toHaveText('3');
  });

  [
    { score: 'RVIS_rank', values: ['2208.5', '2187.5', '449', '383'], columnIndex: 8},
    { score: 'LGD_rank', values: ['10012.5', '1838.5', '737', '299.5'], columnIndex: 9},
    { score: 'pLI_rank', values: ['3433', '2574', '659', '374'], columnIndex: 10},
    { score: 'pRec_rank', values: ['17823', '17507', '14843', '13429'], columnIndex: 11}
  ].forEach(data => {
    test(`should compare protection scores when sort by ${data.score}`, async({ page }) => {
      const row = page.locator('.table-body-row:not(#nothing-found)');
      await searchInGeneProfilesTable(page, 'RAPGEF');
      await expect(row).toHaveCount(4);

      await page.getByText(data.score).click();
      await page.waitForTimeout(200);
      for (let i = 0; i < 4; i++) {
        // eslint-disable-next-line no-await-in-loop
        await expect(row.nth(i).locator('.row-cell').nth(data.columnIndex)).toHaveText(data.values[i]);
      }

      await page.getByText(data.score).click();
      await page.waitForTimeout(200);
      data.values.reverse();
      for (let i = 0; i < 4; i++) {
        // eslint-disable-next-line no-await-in-loop
        await expect(row.nth(i).locator('.row-cell').nth(data.columnIndex)).toHaveText(data.values[i]);
      }
    });
  });

  test('should show nothing found when search query doesn\'t match', async({ page }) => {
    await expect(page.locator('#nothing-found')).not.toBeVisible();

    await searchInGeneProfilesTable(page, 'ewoqoqwekwoqkeowqkeowqkeoqwk');
    await expect(page.locator('#nothing-found')).toBeVisible();

    await page.locator('input#gene-search-input').clear();

    await expect(page.getByText('progress_activity')).not.toBeVisible();

    await expect(page.locator('#nothing-found')).not.toBeVisible();
    const rowCount = await page.locator('.table-body-row:not(#nothing-found)').count();
    expect(rowCount).toBeGreaterThan(1);
  });

  test('should navigate to genotype browser', async({ page }) => {
    await page.getByTitle('7.0 (2.79)\nCHD8').click();
    await page.waitForSelector('gpf-genotype-browser');
    expect(page.url()).toContain('/datasets/iossifov_2014_liftover/genotype-browser');

    await expect(page.locator('#gene-symbols-panel textarea')).toHaveValue('CHD8');
    await expect(page.locator('gpf-pedigree-selector').getByLabel('affected', { exact: true })).toBeChecked();
    await expect(page.locator('gpf-pedigree-selector').getByLabel('unaffected')).not.toBeChecked();

    await expect(page.locator('gpf-effect-types').getByLabel('intron')).not.toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('nonsense')).toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('frame-shift', { exact: true })).toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('splice-site')).toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('no-frame-shift-newStop')).toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('missense')).not.toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('no-frame-shift', { exact: true })).not.toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('noStart')).not.toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('noEnd')).not.toBeChecked();
    await expect(page.locator('gpf-effect-types').getByLabel('synonymous')).not.toBeChecked();

    await expect(page.locator('#variants-count-span')).toHaveText('7 variants selected');
  });

  test('should navigate to genotype browser and check if correct variants are loaded', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Genotype Browser');
    await page.getByRole('tab', { name: 'Gene Symbols' }).click();
    await page.locator('#gene-symbols-panel textarea').pressSequentially('CHD8');
    await page.locator('gpf-pedigree-selector').getByLabel('unaffected').click();

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('7 variants selected');

    await page.locator('#header a:text("Gene Profiles")').click();
    await page.waitForSelector('gpf-gene-profiles-table');

    await page.getByTitle('7.0 (2.79)\nCHD8').click();
    await page.waitForSelector('gpf-genotype-browser');
    expect(page.url()).toContain('/datasets/iossifov_2014_liftover/genotype-browser');

    await expect(page.locator('#variants-count-span')).toHaveText('7 variants selected');
  });
});

// Serial: every test in this block writes to the same user's
// /api/v3/users/user_gp_state row. Running them in parallel lets one
// worker's beforeEach resetGeneProfiles stomp another worker's saved
// state during its logout/login window.
//
// tb-nxl: the per-worker user pool (utils.loginWorkerUser) replaces
// the tb-wtc-era gp_state_test pin — different Playwright workers
// log in as different e2e_worker_<N> users, so the cross-block
// stomping that motivated the dedicated user is gone. .serial here
// remains for intra-block ordering between the three state tests.
test.describe.serial('Gene profiles table state tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await page.locator('#header a:text("Gene Profiles")').click();
    await page.waitForSelector('gpf-gene-profiles-table');
    await page.waitForSelector('#loading', {state: 'detached'});

    await utils.resetGeneProfiles(page);
  });


  test('should check table state when navigating to Genotype browser', async({ page }) => {
    const finalSave = waitForChangeTableSave(page);
    await changeTable(page);
    await finalSave;

    // go to Genotype browser and return to Gene Profiles
    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014Liftover, 'Genotype browser');

    const geneProfilesStateResponse = page.waitForResponse(
      resp => resp.url().includes('/api/v3/users/user_gp_state') && resp.status() === 200
    );

    await page.locator('#header a:text("Gene Profiles")').click();
    await geneProfilesStateResponse;
    await checkTable(page);
  });

  test('should check if table state is saved when logout and login', async({ page }) => {
    const finalSave = waitForChangeTableSave(page);
    await changeTable(page);
    await finalSave;

    await utils.logout(page);
    await page.locator('#header a:text("Gene Profiles")').click();
    await checkDefaultTable(page);

    await utils.loginWorkerUser(page);
    await checkTable(page);
  });

  test('should check reset table button', async({ page }) => {
    const finalSave = waitForChangeTableSave(page);
    await changeTable(page);
    await finalSave;

    await utils.resetGeneProfiles(page);
    await page.waitForSelector('gpf-gene-profiles-table');
    await page.waitForSelector('#loading', {state: 'detached'});
    await checkDefaultTable(page);
  });
});

export async function changeTable(page: Page): Promise<void> {
  // open tab
  await page.locator('div').filter({ hasText: /^GRIN2B$/}).click();
  await page.getByRole('button', {name: 'All genes'}).click();

  await searchInGeneProfilesTable(page, 'RAPGEF');

  // highlight rows and open tab
  await page.keyboard.down('Control');
  await page.locator('.table-body-row').filter({hasText: 'RAPGEF4'}).click();
  await page.locator('.table-body-row').filter({hasText: 'RAPGEF2'}).click();
  await page.keyboard.up('Control');
  await page.locator('#compare-genes-compare-button').click();

  await page.getByRole('button', {name: 'All genes'}).click();

  // change table header columns visibility
  await expect(page.locator('.header-cell')).toHaveCount(25);
  await page.locator('#protection_scores-column-filtering-button').click({force: true});
  await page.waitForSelector('gpf-multiple-select-menu');
  await page.locator('gpf-multiple-select-menu').getByLabel('LGD_rank').click();
  await page.locator('gpf-multiple-select-menu').getByLabel('pLI_rank').click();

  // change table header columns sorting - asc
  await page.getByTitle('Relevant Gene Sets', { exact: true }).click();
  await page.waitForTimeout(200);
  await page.getByTitle('Relevant Gene Sets', { exact: true }).click();
  await page.waitForTimeout(200);


  // change table header columns order
  await page.locator('#relevant_gene_sets_rank-column-filtering-button').click();
  await expect(page.locator('gpf-multiple-select-menu label').nth(0)).toHaveText('CHD8 target genes');

  const columnHeader = page.locator('.header-cell-content-span');
  await expect(columnHeader.nth(5)).toHaveText('CHD8 target genes');

  await page.locator('gpf-multiple-select-menu label').nth(0).hover();
  await page.mouse.down();
  await page.mouse.move(1030, 370, {steps: 3});
  await page.mouse.up();

  await expect(page.locator('gpf-multiple-select-menu label').nth(2)).toHaveText('CHD8 target genes');
  await expect(columnHeader.nth(7)).toHaveText('CHD8 target genes');
}

// Wait for the trailing debounced save that includes changeTable()'s
// FINAL drag-drop column reorder. gene-profiles-table.service.ts uses a
// 1s trailing-edge debouncer, so a single fingerprint on the post-drag
// header order uniquely identifies the trailing save and subsumes every
// earlier mutation.
//
// The drag-drop in changeTable() moves CHD8 target genes within the
// relevant_gene_sets_rank group, from FIRST sub-leaf (before chromatin
// modifiers) to a LATER position (after chromatin modifiers). Default
// order has CHD8 first; post-drag has chromatin first.
export function waitForChangeTableSave(page: Page): Promise<Response> {
  return page.waitForResponse(resp => {
    if (!resp.url().includes('/api/v3/users/user_gp_state')) {
      return false;
    }
    if (resp.request().method() !== 'POST') {
      return false;
    }
    if (resp.status() !== 204) {
      return false;
    }
    const body = resp.request().postDataJSON() as GeneProfilesState | null;
    if (!body?.headerLeaves) {
      return false;
    }
    const idxChd8 = body.headerLeaves.indexOf(
      'relevant_gene_sets_rank.CHD8 target genes',
    );
    const idxChromatin = body.headerLeaves.indexOf(
      'relevant_gene_sets_rank.chromatin modifiers',
    );
    return idxChd8 > 0 && idxChromatin > 0 && idxChd8 > idxChromatin;
  });
}

async function checkDefaultTable(page: Page): Promise<void> {
  await expect(page.locator('input#gene-search-input')).toBeEmpty();// check search and search result
  await expect(page.locator('.table-body-row:not(#nothing-found)')).toHaveCount(16);
  await expect(page.locator('#compare-genes-modal')).not.toBeVisible(); // check highlighted rows
  await expect(page.locator('.header-cell')).toHaveCount(25);// check column visibility
  await expect(page.locator('div.tab')).toHaveCount(0);// check opened tabs
  await expect(page.locator('div.active-sort-header')).toContainText('Autism Gene Sets'); // check sorting
  await expect(page.locator('div.active-sort-header').locator('gpf-sorting-buttons span')).toHaveId('desc');
  await expect(page.locator('.header-cell-content-span').nth(5))
    .toHaveText('CHD8 target genes');// check column reorder
}

export async function checkTable(page: Page): Promise<void> {
  const columnHeader = page.locator('.header-cell-content-span');
  // check search and search result
  await expect(page.locator('input#gene-search-input')).toHaveValue('RAPGEF');
  await expect(page.locator('.table-body-row:not(#nothing-found)')).toHaveCount(4);

  // check highlighted rows
  await expect(page.locator('.table-body-row').filter({hasText: 'RAPGEF4'}))
    .toHaveClass(/row-highlight/);
  await expect(page.locator('.table-body-row').filter({hasText: 'RAPGEF2'}))
    .toHaveClass(/row-highlight/);

  // check column visibility
  await expect(page.locator('.header-cell')).toHaveCount(23);
  await expect(page.locator('.header-cell').filter({ hasText: 'LGD_rank'})).not.toBeVisible();
  await expect(page.locator('.header-cell').filter({ hasText: 'pLI_rank'})).not.toBeVisible();

  // check opened tabs
  await expect(page.locator('div.tab')).toHaveCount(2);
  await expect(page.locator('div.tab').nth(0)).toContainText('GRIN2B');
  await expect(page.locator('div.tab').nth(1)).toContainText('RAPGEF2,RAPGEF4');

  // check sorting
  await expect(page.locator('div.active-sort-header')).toContainText('Relevant Gene Sets');
  await expect(page.locator('div.active-sort-header').locator('gpf-sorting-buttons span')).toHaveId('asc');

  // check column reorder
  await page.locator('#relevant_gene_sets_rank-column-filtering-button').click();
  await expect(page.locator('gpf-multiple-select-menu label').nth(2)).toHaveText('CHD8 target genes');
  await expect(columnHeader.nth(7)).toHaveText('CHD8 target genes');
}