import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Family filters block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('should display family ids panel', async({ page }) => {
    await expect(page.locator('#family-ids-panel')).not.toBeVisible();
    await page.locator('#family-ids').click();
    await expect(page.locator('#family-ids-panel')).toBeVisible();
  });

  test('should display error alert in family ids panel when the textarea is empty', async({ page }) => {
    await page.locator('#family-ids').click();
    await expect(page.getByText('Please insert at least one family id.')).toBeVisible();

    await page.locator('gpf-family-ids textarea').pressSequentially('f1');
    await expect(page.getByText('Please insert at least one family id.')).not.toBeVisible();

    await page.locator('gpf-family-ids textarea').clear();
    await expect(page.getByText('Please insert at least one family id.')).toBeVisible();
  });

  test('should test save/share query after entering family ids', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Ids')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Ids').click();

    await page.locator('gpf-family-ids textarea').focus();
    await page.keyboard.type('14338');

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('1 variant selected');

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#link-input')).not.toHaveValue('');
    const url = await page.locator('#link-input').inputValue();
    await page.goto(url);

    await expect(page.locator('gpf-family-ids textarea')).toHaveText('14338');

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('1 variant selected');
  });

  test('should test resetting family ids state', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Ids')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Ids').click();

    await page.locator('gpf-family-ids textarea').focus();
    await page.keyboard.type('f1, f2');

    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();

    await page.locator('gpf-family-filters-block').getByText('All').click();

    await page.locator('gpf-family-filters-block').getByText('Family Ids').click();
    await expect(page.locator('gpf-family-ids textarea')).toBeEmpty();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('should test family ids error state is reset when switching tab', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Ids')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Ids').click();

    await expect(page.getByText('Please insert at least one family id.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('gpf-family-filters-block').getByText('All').click();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();
  });

  test('should check number of selected variants when changing list of ids and if table is reset', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Ids')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Ids').click();

    await page.locator('gpf-family-ids textarea').focus();
    await page.keyboard.type('f5');

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('2 variants selected');

    await page.locator('gpf-family-ids textarea').focus();
    await page.keyboard.type(', f7');
    await expect(page.locator('gpf-genotype-preview-table')).not.toBeVisible();

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('3 variants selected');
  });

  test('should preview table and download filtered by Family Tags', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Tags')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Tags').click();

    await expect(page.locator('gpf-family-filters-block').locator('gpf-family-tags')).toBeVisible();

    await page.locator('#tag_nuclear_family-tag-add').click();
    await page.locator('#tag_quad_family-tag-remove').click();

    await page.locator('#table-preview-button').click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('76 variants selected', { timeout: 120000 });


    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.locator('#download-button').click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(
      'playwright/fixtures/genotype-browser/variants-2.tsv',
      {
        sep: '\t',
        inferSchemaLength: 0
      });
    const downloadData = scanCSV(await download.path(), {sep: '\t', inferSchemaLength: 0});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should preview table and download filtered by Family Tags and mode "Or"', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Tags')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Tags').click();

    await expect(page.locator('gpf-family-filters-block').locator('gpf-family-tags')).toBeVisible();

    await page.locator('.or-toggle-button').click();

    await page.locator('#tag_nuclear_family-tag-remove').click();
    await page.locator('#tag_quad_family-tag-add').click();
    await page.locator('#tag_missing_dad_family-tag-add').click();

    await page.locator('#table-preview-button').click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('496 variants selected', { timeout: 120000 });


    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.locator('#download-button').click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(
      'playwright/fixtures/genotype-browser/variants-3.tsv',
      {
        sep: '\t',
        inferSchemaLength: 0
      });
    const downloadData = scanCSV(await download.path(), {sep: '\t', inferSchemaLength: 0});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should test save/share query after selecting Family tags', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Tags')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Tags').click();

    await page.locator('.or-toggle-button').click();

    await page.locator('#tag_nuclear_family-tag-remove').click();
    await page.locator('#tag_affected_dad_family-tag-add').click();
    await page.locator('#tag_quad_family-tag-add').click();
    await page.locator('#tag_affected_mom_family-tag-add').click();
    await page.locator('#tag_affected_prb_family-tag-remove').click();
    await page.locator('#tag_affected_sib_family-tag-remove').click();
    await page.locator('#tag_unaffected_prb_family-tag-add').click();
    await page.locator('#tag_missing_dad_family-tag-add').click();

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#link-input')).not.toHaveValue('');
    const url = await page.locator('#link-input').inputValue();
    await page.goto(url);
    await page.waitForSelector('gpf-genotype-browser');

    await expect(page.locator('#tag_nuclear_family-tag-remove')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(page.locator('#tag_affected_dad_family-tag-add')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(page.locator('#tag_quad_family-tag-add')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(page.locator('#tag_affected_mom_family-tag-add')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(page.locator('#tag_affected_prb_family-tag-remove')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(page.locator('#tag_affected_sib_family-tag-remove')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(page.locator('#tag_unaffected_prb_family-tag-add')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(page.locator('#tag_missing_dad_family-tag-add')).toHaveCSS('color', 'rgb(0, 128, 0)');
  });

  test('should clear all tags that are selected in Family Tags', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Family Tags')).toBeVisible();
    await page.locator('gpf-family-filters-block').getByText('Family Tags').click();

    await expect(page.locator('gpf-family-filters-block').locator('gpf-family-tags')).toBeVisible();

    await page.locator('#tag_nuclear_family-tag-add').click();
    await page.locator('#tag_quad_family-tag-remove').click();

    await page.locator('#table-preview-button').click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('76 variants selected', { timeout: 120000 });

    await page.locator('#clear-filters-button').click();
    await expect(page.locator('#tag_nuclear_family-tag-add')).not.toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(page.locator('#tag_quad_family-tag-remove')).not.toHaveCSS('color', 'rgb(255, 0, 0)');

    await page.locator('#table-preview-button').click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('572 variants selected', { timeout: 120000 });
  });

  test('should display pheno filters panel after "Advanced" button click', async({ page }) => {
    await expect(page.locator('gpf-family-filters-block')
      .getByRole('tab', { name: 'Advanced', exact: true })).toBeVisible();
    await page.locator('gpf-family-filters-block').getByRole('tab', { name: 'Advanced', exact: true }).click();

    await expect(page.locator('gpf-family-filters-block').locator('gpf-multi-continuous-filter')).toBeVisible();
    await expect(page.getByText('Select at least one continuous filter.')).toBeVisible();

    await page.locator('gpf-family-filters-block').locator('#search-box').click();
    await page.locator('.dropdown-item span', {hasText: 'instrument_1.age'}).click();
    await expect(page.locator('gpf-histogram')).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block')
      .getByRole('tab', { name: 'Advanced', exact: true })).not.toBeVisible();
  });

  test('errors state reset when opening Pheno Measures tab and switch tool', async({ page }) => {
    await expect(page.locator('gpf-family-filters-block')
      .getByRole('tab', { name: 'Pheno Measures', exact: true })).toBeVisible();
    await page.locator('gpf-family-filters-block').getByRole('tab', { name: 'Pheno Measures', exact: true }).click();

    await expect(page.locator('gpf-person-filters-selector')).toBeVisible();
    await expect(page.getByText('Select a measure.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();

    await page.locator('a').filter({ hasText: 'Gene browser'}).click();

    await page.locator('a').filter({ hasText: 'Genotype browser'}).click();
    await expect(page.locator('gpf-family-filters-block')
      .getByRole('tab', { name: 'Pheno Measures', exact: true })).toBeVisible();

    await expect(page.locator('gpf-person-filters-selector')).not.toBeVisible();
    await expect(page.getByText('Select a measure.')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
  });
});

test.describe('Pheno Measures tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('pheno measures panel', async({ page }) => {
    await expect(page.locator('#pheno-filters-panel')).not.toBeVisible();
    await page.locator('gpf-family-filters-block #phenoMeasures').click();
    await expect(page.locator('#pheno-filters-panel')).toBeVisible();
    await expect(page.getByText('Select a measure.')).toBeVisible();
    await expect(page.locator('#measures-dropdown')).toBeVisible();
  });

  test('if Pheno Measures tab is enabled in Genotype browser for different studies', async({ page }) => {
    await utils.navigateToDatasetPage(page, datasetIds.allGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Pheno Measures')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Pheno Measures')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Pheno Measures')).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');
    await expect(page.locator('gpf-family-filters-block').getByText('Pheno Measures')).toBeVisible();
  });

  test('measures order and dropdown content update when adding measures', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_3').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_1').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.iq')).not.toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_3')).not.toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_1')).not.toBeVisible();

    await expect(page.locator('gpf-person-filter')).toHaveCount(3);
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_1');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.measure_3');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(2)).toContainText('instrument_1.iq');
  });

  test('measures order and dropdown content update when removing measures', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_4').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(3);

    await page.locator('[id="instrument_2\\.measure_6-remove-button"]').click();
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_4');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.age');

    await page.locator('[id="instrument_1\\.age-remove-button"]').click();
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_4');

    await page.locator('[id="instrument_1\\.measure_4-remove-button"]').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(0);
    await page.getByPlaceholder('Select or start typing to').click();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.age')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_2.measure_6')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_4')).toBeVisible();
  });

  test('searching and selecting pheno measure', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').focus();
    await page.keyboard.type('iq');

    await expect(page.locator('.measures-dropdown').getByText('instrument_1.iq')).toBeVisible();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();
    await expect(
      page.locator('gpf-family-filters-block').getByRole('textbox', { name: 'Select or start typing to' })
    ).toBeEmpty();
    await expect(page.locator('gpf-person-filter')).toContainText('instrument_1.iq');
  });

  test('searching and selecting pheno measure with arrows and enter', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').focus();
    await page.keyboard.type('measure');

    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_1')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_2')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_3')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_4')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_1.measure_5')).toBeVisible();
    await expect(page.locator('.measures-dropdown').getByText('instrument_2.measure_6')).toBeVisible();

    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');

    await expect(page.locator('gpf-person-filter')).toContainText('instrument_1.measure_3');
  });
  test('searching invalid pheno measure', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').focus();
    await page.keyboard.type('invalidMeasure');

    await expect(page.locator('.measures-dropdown').getByText('Nothing found')).toBeVisible();
    await expect(page.getByText('Select a measure.')).toBeVisible();
  });

  test('resetting pheno measures state when changing tab', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);

    await page.locator('gpf-family-filters-block').getByText('All').click();
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await expect(page.locator('gpf-person-filter')).toHaveCount(0);
    await expect(page.getByText('Select a measure.')).toBeVisible();
  });

  test('resetting pheno measures state when changing tool', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();

    await page.getByText('Phenotype browser').click();
    await page.getByText('Genotype browser').click();
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(0);
    await expect(page.getByText('Select a measure.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('resetting invalid pheno measures continuous histogram state when changing tab', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);

    await page.locator('gpf-person-filter').nth(0).locator('#from-input-field').clear();
    await page.locator('gpf-person-filter').nth(0).locator('#from-input-field').pressSequentially('-100');

    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('gpf-family-filters-block').getByText('All').click();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();

    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await expect(page.locator('gpf-person-filter')).toHaveCount(0);
    await expect(page.getByText('Select a measure.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('resetting invalid pheno measures categorical histogram state when changing tab', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_5').click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();

    await expect(page.getByText('Please select at least one value.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('gpf-family-filters-block').getByText('All').click();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();

    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await expect(page.locator('gpf-person-filter')).toHaveCount(0);
    await expect(page.getByText('Select a measure.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();
  });

  test('if error state is reset when removing histogram in invalid state', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_2.measure_6' })
      .getByPlaceholder('start').clear();
    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_2.measure_6' })
      .getByPlaceholder('start').fill('-100');
    await expect(page.getByText('Range start should be more than or equal to domain min.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeDisabled();

    await page.locator('[id="instrument_2.measure_6-remove-button"]').click();

    await expect(page.getByRole('button', { name: 'Table Preview'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Share/save query'})).toBeEnabled();
    await expect(page.getByRole('button', { name: 'Download'})).toBeEnabled();
  });

  test('downloaded file with multiple selected pheno measures', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_1').click();

    const measure1 = page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_1' });

    await measure1.locator('#from-input-field').clear();
    await measure1.locator('#from-input-field').pressSequentially('47.141');
    await measure1.locator('#to-input-field').clear();
    await measure1.locator('#to-input-field').pressSequentially('60.839');

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.age').click();

    const measure2 = page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.age' });

    await measure2.locator('#to-input-field').clear();
    await measure2.locator('#to-input-field').pressSequentially('111.06');

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('playwright/fixtures/genotype-browser/variants-5.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('share/save query with multiple selected pheno measures', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_5').click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(3);
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_5');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.iq');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(2)).toContainText('instrument_2.measure_6');

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#link-input')).not.toHaveValue('');
    const url = await page.locator('#link-input').inputValue();
    await page.goto(url);
    await page.waitForSelector('gpf-genotype-browser');

    await expect(page.locator('gpf-person-filter')).toHaveCount(3);
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_5');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.iq');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(2)).toContainText('instrument_2.measure_6');
  });

  test('select role and check downloaded file', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_5').click();

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_5' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'sib'}).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="val4"]').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('playwright/fixtures/genotype-browser/variants-4.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('select measures and roles and check loaded query', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_4').click();

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_4' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'mom'}).click();
    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_4' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'dad'}).click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_5').click();

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_5' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'sib'}).click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_5');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.measure_4');

    await page.locator('#save-query-dropdown-button').click();
    await expect(page.locator('#link-input')).not.toHaveValue('');
    const url = await page.locator('#link-input').inputValue();
    await page.goto(url);
    await page.waitForSelector('gpf-genotype-browser');

    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_5');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.measure_4');
    await expect(page.locator('#roles-list').nth(0).locator('.role-wrapper')).toContainText('sib');
    await expect(page.locator('#roles-list').nth(1).locator('.role-wrapper').nth(0)).toContainText('mom');
    await expect(page.locator('#roles-list').nth(1).locator('.role-wrapper').nth(1)).toContainText('dad');
  });

  test('selecting role and checking histogram', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await expect(page.locator('#sumOfBarsLabel')).toHaveText('~191 (100.00%)');
    await expect(page.locator('.histogram-from label')).toHaveText('From (Min: -11.1093)');
    await expect(page.locator('.histogram-to label')).toHaveText('To (Max: 174.2897)');

    await page.locator('gpf-role-selector #search-box').click();
    await page.locator('mat-option').getByText('prb').click();
    await expect(page.locator('#sumOfBarsLabel')).toHaveText('~39 (100.00%)');
    await expect(page.locator('.histogram-from label')).toHaveText('From (Min: 12.9578)');
    await expect(page.locator('.histogram-to label')).toHaveText('To (Max: 150.2109)');
  });

  test('selecting, removing and updating dropdown enabled roles', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.locator('gpf-role-selector #search-box').click();
    await page.getByRole('option', {name: 'prb'}).click();

    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.getByRole('option', {name: 'prb'})).toBeDisabled();
    await page.getByRole('option', {name: 'mom'}).click();

    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.getByRole('option', {name: 'mom'})).toBeDisabled();
    await page.locator('gpf-role-selector #search-box').blur();

    await expect(page.locator('.role-wrapper')).toHaveCount(2);
    await expect(page.locator('.role-wrapper').nth(0)).toContainText('prb');
    await expect(page.locator('.role-wrapper').nth(1)).toContainText('mom');

    await page.locator('#remove-prb').click();
    await expect(page.locator('.role-wrapper')).toHaveCount(1);
    await expect(page.locator('.role-wrapper').nth(0)).toContainText('mom');

    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.getByRole('option', {name: 'prb'})).toBeEnabled();
    await page.locator('gpf-role-selector #search-box').blur();

    await page.locator('#remove-mom').click();
    await expect(page.locator('.role-wrapper')).toHaveCount(0);
    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.locator('mat-option').getByText('mom')).toBeEnabled();
    await page.locator('gpf-role-selector #search-box').blur();
  });

  test('selecting role by typing and enter', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.locator('gpf-role-selector #search-box').focus();
    await page.keyboard.type('mo');
    await expect(page.getByRole('option', {name: 'mom'})).toBeVisible();
    await expect(page.getByRole('option', {name: 'dad'})).toBeHidden();
    await expect(page.getByRole('option', {name: 'prb'})).toBeHidden();
    await expect(page.getByRole('option', {name: 'sib'})).toBeHidden();

    await page.keyboard.press('Enter');
    await expect(page.locator('gpf-role-selector #search-box')).toBeEmpty();
    await expect(page.locator('.role-wrapper')).toHaveCount(1);
    await expect(page.locator('.role-wrapper').nth(0)).toContainText('mom');

    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.getByRole('option', {name: 'mom'})).toBeDisabled();
    await expect(page.getByRole('option', {name: 'dad'})).toBeEnabled();
    await expect(page.getByRole('option', {name: 'prb'})).toBeEnabled();
    await expect(page.getByRole('option', {name: 'sib'})).toBeEnabled();
    await page.locator('gpf-role-selector #search-box').blur();
  });

  test('typing invalid role', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.locator('gpf-role-selector #search-box').focus();
    await page.keyboard.type('po');
    await expect(page.getByRole('option')).toHaveCount(0);

    await page.keyboard.press('Enter');
    await expect(page.locator('.role-wrapper')).toHaveCount(0);
    await expect(page.locator('gpf-role-selector #search-box')).toBeEmpty();

    await page.locator('gpf-role-selector #search-box').click();
    await expect(page.getByRole('option', {name: 'mom'})).toBeEnabled();
    await expect(page.getByRole('option', {name: 'dad'})).toBeEnabled();
    await expect(page.getByRole('option', {name: 'prb'})).toBeEnabled();
    await expect(page.getByRole('option', {name: 'sib'})).toBeEnabled();
    await page.locator('gpf-role-selector #search-box').blur();
  });

  test('histograms order when updating roles list of a measure', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.iq').click();

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.iq' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'mom'}).click();

    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_3').click();

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.measure_3' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'dad'}).click();

    await expect(page.locator('gpf-person-filter')).toHaveCount(2);
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_3');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.iq');

    await page.locator('gpf-person-filter').filter({ hasText: 'instrument_1.iq' })
      .getByPlaceholder('Select role').click();
    await page.getByRole('option', {name: 'sib'}).click();
    await page.locator('#remove-mom').click();

    await expect(page.locator('gpf-person-filter .title-wrapper').nth(0)).toContainText('instrument_1.measure_3');
    await expect(page.locator('gpf-person-filter .title-wrapper').nth(1)).toContainText('instrument_1.iq');
    await expect(page.locator('#roles-list').nth(0).locator('.role-wrapper')).toContainText('dad');
    await expect(page.locator('#roles-list').nth(1).locator('.role-wrapper')).toContainText('sib');
  });

  test('filtering by pheno measures in family filters and person filters', async({ page }) => {
    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_1').click();

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('6 variants selected');

    await page.locator('gpf-person-filters-block').getByText('Pheno Measures').click();
    await page.locator('gpf-person-filters-block').getByRole('textbox', { name: 'Select or start typing to' }).click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    await page.getByRole('button', { name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span')).toHaveText('4 variants selected');
  });

  test('filtering by pheno measures in Phenotype Tool', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Phenotype tool');
    await page.locator('input#search-box').click();
    await page.getByText('instrument_1.age').click();

    await page.locator('gpf-family-filters-block').getByText('Pheno Measures').click();
    await page.locator('gpf-family-filters-block').getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_1.measure_4').click();

    await page.locator('gpf-family-filters-block').getByPlaceholder('Select or start typing to').click();
    await page.locator('.measures-dropdown').getByText('instrument_2.measure_6').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByRole('button', {name: 'Download'}).click();
    const download = await downloadPromise;

    const fixtureData = scanCSV('playwright/fixtures/pheno-tool/pheno_report18.csv');
    const downloadData = scanCSV(await download.path());
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});