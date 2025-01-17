import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Genomic scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
  });

  test('should display genomic scores panel after "add filter" button click ' +
  'and remove it after "remove filter" button click', async({ page }) => {
    await expect(page.locator('gpf-genomic-scores')).toBeHidden();

    await page.locator('#add-filter').click();
    await expect(page.locator('gpf-genomic-scores')).toBeVisible();

    await page.locator('#remove-button').click();
    await expect(page.locator('gpf-genomic-scores')).toBeHidden();
  });

  test('should enter filter data and check how it affects the histogram', async({ page }) => {
    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
      'A deleteriousness prediction score for missense variants';
    await page.locator('#add-filter').click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}")`).click();

    await page.locator('input#from-input-field').clear();
    await page.locator('input#from-input-field').fill('0.3');
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~21727789 (32.46%)');

    await page.locator('input#to-input-field').clear();
    await page.locator('input#to-input-field').fill('1.45');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~9402408 (14.05%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~35798106 (53.49%)');

    const exomeGnomadScore = 'exome_gnomad_af_percent - ' +
      'Alternative allele frequency in the whole gnomAD exome samples v2.1.1 as percent';
    await page.locator('gpf-genomic-scores-block >> #add-filter').click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').nth(1).click();
    await page.locator(`mat-option:has-text("${exomeGnomadScore}")`).click();

    await page.locator('input#from-input-field').nth(1).clear();
    await page.locator('input#from-input-field').nth(1).fill('9.7944');
    await expect(page.locator('text.partitions-text').nth(3)).toHaveText('~17113188 (99.46%)');

    await page.locator('input#to-input-field').nth(1).clear();
    await page.locator('input#to-input-field').nth(1).fill('13.6935');
    await expect(page.locator('text.partitions-text').nth(4)).toHaveText('~82289 (0.48%)');
    await expect(page.locator('text.partitions-text').nth(5)).toHaveText('~10162 (0.06%)');

    await page.locator('#remove-button').nth(0).click();
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~17113188 (99.46%)');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~82289 (0.48%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~10162 (0.06%)');
  });

  test('should test download', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';
    await page.locator('#add-filter').click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}")`).click();

    await page.locator('input#from-input-field').clear();
    await page.locator('input#from-input-field').fill('1.25');

    await page.locator('input#to-input-field').clear();
    await page.locator('input#to-input-field').fill('1.8');

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('playwright/fixtures/genomic-scores/variants.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});