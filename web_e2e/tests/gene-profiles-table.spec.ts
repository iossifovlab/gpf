import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Gene profiles row data tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });

  // refactor;
  // on test failure caused by a value change in the row,
  // it's hard to track in which specific column the change has occured
  [
    {geneSymbol: 'CHD8', expectedRow: 'CHD8✓✓✓✓✓11938331.5181787.0 (2.79)'},
    {geneSymbol: 'SHANK2', expectedRow: 'SHANK2✓✓✓143649175171.0 (0.4)1.0 (0.52)'},
    {geneSymbol: 'FLG', expectedRow: 'FLG✓1664018394.51.0 (0.4)'},
    {geneSymbol: 'CMIP', expectedRow: 'CMIP✓3558249469417467'},
    {geneSymbol: 'TBCD', expectedRow: 'TBCD✓6469111.513275.52222.0 (1.05)'}
  ].forEach(data => {
    test(`should display correct gene data for ${data.geneSymbol}`, async({ page }) => {
      await page.locator('input#gene-search-input').focus();
      await page.keyboard.type(data.geneSymbol);
      await expect(page.locator('.table-body-row:not(#nothing-found)')).toHaveCount(1);
      await expect(page.locator('.table-body-row').first()).toHaveText(data.expectedRow.replace(/✓/g, 'check_small'));
    });
  });
});

test.describe('Gene profiles table column filtering tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
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
    await page.locator('gpf-multiple-select-menu').getByLabel('iossifov_2014').click();
    await expect(headerCell.getByText('iossifov_2014', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('affected (2507)', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('unaffected (1910)', { exact: true})).not.toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('LGDs', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('missense', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(0)).not.toBeVisible();
    await expect(headerCell.getByText('intron', { exact: true}).nth(1)).not.toBeVisible();
    await expect(headerCell).toHaveCount(16);

    await page.locator('gpf-multiple-select-menu').getByLabel('iossifov_2014').click();
    await expect(headerCell.getByText('iossifov_2014', { exact: true})).toBeVisible();
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
    await page.mouse.move(430, 230, {steps: 2});
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
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });
  test('should highlight a row using control+click and change it\'s background color', async({ page }) => {
    const firstRow = page.locator('.table-body-row:not(#nothing-found)').nth(0);
    await expect(firstRow).toHaveClass('table-row table-body-row');

    await page.keyboard.down('Control');
    await firstRow.click();

    // hover another row to check the background color
    await page.locator('.table-body-row:not(#nothing-found)').nth(1).hover();
    await expect(firstRow).toHaveClass('table-row table-body-row row-highlight');
    await expect(firstRow).toHaveCSS('background-color', oddHighlightColor);

    await page.keyboard.down('Control');
    await firstRow.click();

    // hover another row to check the background color
    await page.locator('.table-body-row:not(#nothing-found)').nth(1).hover();
    await expect(firstRow).toHaveClass('table-row table-body-row');
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

    await expect(row.nth(0)).toHaveClass('table-row table-body-row row-highlight');
    await expect(row.nth(1)).toHaveClass('table-row table-body-row row-highlight');
    await expect(row.nth(2)).toHaveClass('table-row table-body-row row-highlight');
    await page.keyboard.up('Control');

    await page.keyboard.press('Escape');
    await expect(row.nth(0)).toHaveClass('table-row table-body-row');
    await expect(row.nth(1)).toHaveClass('table-row table-body-row');
    await expect(row.nth(2)).toHaveClass('table-row table-body-row');
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
    await expect(row.nth(0)).toHaveClass('table-row table-body-row');
    await expect(page.locator('.compare-gene-item')).toHaveCount(2);

    await page.locator('.compare-genes-close').nth(0).click();
    await expect(row.nth(1)).toHaveClass('table-row table-body-row');
    await expect(page.locator('.compare-gene-item')).toHaveCount(1);

    await page.locator('.compare-genes-close').nth(0).click();
    await expect(row.nth(2)).toHaveClass('table-row table-body-row');
    await expect(row).not.toBeVisible();
  });
});

test.describe('Gene profiles table functionality tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await page.locator('#header a:text("Gene Profiles")').click();
  });
  test('should sort genes by autism gene sets', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('RAPGEF');
    await expect(row).toHaveCount(4);

    await page.locator('#category-filtering-button').click();
    await page.locator('#check-uncheck-all-button').click();
    await page.getByLabel('Autism Gene Sets').click();
    await page.locator('#category-filtering-button').click();

    await expect(row.nth(0).locator('.row-cell').nth(0)).toHaveText('RAPGEF4');
    await expect(row.nth(0).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(0).locator('.row-cell').nth(2)).toHaveText('');
    await expect(row.nth(1)).toHaveText('RAPGEF2');
    await expect(row.nth(2)).toHaveText('RAPGEFL1');
    await expect(row.nth(3)).toHaveText('RAPGEF1');

    await page.locator('.header-cell').getByText('Autism Gene Sets').click();
    await page.waitForTimeout(200);
    await expect(row.nth(0)).toHaveText('RAPGEF2');
    await expect(row.nth(1)).toHaveText('RAPGEFL1');
    await expect(row.nth(2)).toHaveText('RAPGEF1');
    await expect(row.nth(3).locator('.row-cell').nth(0)).toHaveText('RAPGEF4');
    await expect(row.nth(3).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(3).locator('.row-cell').nth(2)).toHaveText('');
  });

  test('should sort genes by relevant gene sets', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('SENP');
    await expect(row).toHaveCount(6);

    await page.locator('#category-filtering-button').click();
    await page.locator('#check-uncheck-all-button').click();
    await page.getByLabel('Relevant Gene Sets').click();
    await page.locator('#category-filtering-button').click();

    await page.locator('.header-cell').getByText('Relevant Gene Sets').click();
    await page.waitForTimeout(200);

    await expect(row.nth(0).locator('.row-cell').nth(0)).toHaveText('SENP1');
    await expect(row.nth(0).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(0).locator('.row-cell').nth(3)).toHaveText('check_small');

    await expect(row.nth(1).locator('.row-cell').nth(0)).toHaveText('SENP6');
    await expect(row.nth(1).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(1).locator('.row-cell').nth(2)).toHaveText('');

    await expect(row.nth(2).locator('.row-cell').nth(0)).toHaveText('SENP2');
    await expect(row.nth(2).locator('.row-cell').nth(3)).toHaveText('check_small');

    await expect(row.nth(3).locator('.row-cell').nth(0)).toHaveText('SENP8');
    await expect(row.nth(3).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(4).locator('.row-cell').nth(0)).toHaveText('SENP3-EIF4A1');
    await expect(row.nth(4).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(5).locator('.row-cell').nth(0)).toHaveText('SENP3');
    await expect(row.nth(5).locator('.row-cell').nth(1)).toHaveText('check_small');

    await page.locator('.header-cell').getByText('Relevant Gene Sets').click();
    await page.waitForTimeout(200);

    await expect(row.nth(0).locator('.row-cell').nth(0)).toHaveText('SENP6');
    await expect(row.nth(0).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(1).locator('.row-cell').nth(0)).toHaveText('SENP2');
    await expect(row.nth(1).locator('.row-cell').nth(3)).toHaveText('check_small');

    await expect(row.nth(2).locator('.row-cell').nth(0)).toHaveText('SENP8');
    await expect(row.nth(2).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(3).locator('.row-cell').nth(0)).toHaveText('SENP3-EIF4A1');
    await expect(row.nth(3).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(4).locator('.row-cell').nth(0)).toHaveText('SENP3');
    await expect(row.nth(4).locator('.row-cell').nth(1)).toHaveText('check_small');

    await expect(row.nth(5).locator('.row-cell').nth(0)).toHaveText('SENP1');
    await expect(row.nth(5).locator('.row-cell').nth(1)).toHaveText('check_small');
    await expect(row.nth(5).locator('.row-cell').nth(3)).toHaveText('check_small');
  });

  test('should test autism scores', async({ page }) => {
    const row = page.locator('.table-body-row:not(#nothing-found)');
    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('CHD');
    await expect(row).toHaveCount(15);

    await page.getByText('SFARI gene score').click();
    await page.waitForTimeout(200);
    await expect(row.nth(0).locator('.row-cell').nth(7)).toHaveText('3');
    await expect(row.nth(1).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(2).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(3).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(4).locator('.row-cell').nth(7)).toHaveText('1');

    await page.getByText('SFARI gene score').click();
    await page.waitForTimeout(200);
    await expect(row.nth(0).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(1).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(2).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(3).locator('.row-cell').nth(7)).toHaveText('1');
    await expect(row.nth(4).locator('.row-cell').nth(7)).toHaveText('3');

    for (let i = 5; i < 15; i++) {
      // eslint-disable-next-line no-await-in-loop
      await expect(row.nth(i).locator('.row-cell').nth(7)).toHaveText('');
    }
  });

  [
    { score: 'RVIS_rank', values: ['2208.5', '2187.5', '449', '383'], columnIndex: 8},
    { score: 'LGD_rank', values: ['10012.5', '1838.5', '737', '299.5'], columnIndex: 9},
    { score: 'pLI_rank', values: ['3433', '2574', '659', '374'], columnIndex: 10},
    { score: 'pRec_rank', values: ['17823', '17507', '14843', '13429'], columnIndex: 11}
  ].forEach(data => {
    test(`should compare protection scores when sort by ${data.score}`, async({ page }) => {
      const row = page.locator('.table-body-row:not(#nothing-found)');
      await page.locator('input#gene-search-input').focus();
      await page.keyboard.type('RAPGEF');
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

    await page.locator('input#gene-search-input').focus();
    await page.keyboard.type('ewoqoqwekwoqkeowqkeowqkeoqwk');
    await expect(page.locator('#nothing-found')).toBeVisible();

    await page.locator('input#gene-search-input').clear();
    await expect(page.locator('#nothing-found')).not.toBeVisible();
    const rowCount = await page.locator('.table-body-row:not(#nothing-found)').count();
    expect(rowCount).toBeGreaterThan(1);
  });
});