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

    await page.locator('gpf-family-ids textarea').fill('f1');
    await expect(page.getByText('Please insert at least one family id.')).not.toBeVisible();
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
});