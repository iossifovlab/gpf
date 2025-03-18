import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Genomic scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAllLiftover, 'Genotype browser');
  });

  test('should display genomic scores panel after selecting score ' +
  'and remove it after "remove filter" button click', async({ page }) => {
    await expect(page.locator('gpf-genomic-scores')).toBeHidden();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator('mat-option').nth(0).click();

    await expect(page.locator('gpf-genomic-scores')).toBeVisible();

    await page.locator('#remove-button').click();
    await expect(page.locator('gpf-genomic-scores')).toBeHidden();
  });

  test('should enter filter data and check how it affects the histogram', async({ page }) => {
    const exomeGnomadScore = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${exomeGnomadScore}")`).click();

    await page.locator('input#from-input-field').nth(0).clear();
    await page.locator('input#from-input-field').nth(0).fill('0.063');
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~74244341 (97.47%)');

    await page.locator('input#to-input-field').nth(0).clear();
    await page.locator('input#to-input-field').nth(0).fill('1.096');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~840182 (1.10%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~1090009 (1.43%)');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
      'A deleteriousness prediction score for missense variants';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}")`).click();

    await page.locator('input#from-input-field').nth(0).clear();
    await page.locator('input#from-input-field').nth(0).fill('0.3');
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~21727789 (32.46%)');

    await page.locator('input#to-input-field').nth(0).clear();
    await page.locator('input#to-input-field').nth(0).fill('1.45');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~9402408 (14.05%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~35798106 (53.49%)');

    await page.locator('#remove-button').nth(0).click();
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~74244341 (97.47%)');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~840182 (1.10%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~1090009 (1.43%)');
  });

  test('should test download', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

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