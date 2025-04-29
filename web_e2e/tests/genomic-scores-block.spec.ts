import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Genomic scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
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

  test('should select categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();
    await expect(page.locator('gpf-genomic-scores')).toBeVisible();
    await expect(page.locator('gpf-helper-modal')).toBeVisible();
    await expect(page.getByRole('button', {name: 'Mode'})).toBeVisible();
    await expect(page.locator('gpf-categorical-histogram')).toBeVisible();
    await expect(page.locator('gpf-remove-button')).toBeVisible();
  });

  test('should check histograms order when adding new histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    const gnomad_exomes = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpc}")`).click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomad_exomes}")`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(gnomad_exomes);
    await expect(page.locator('gpf-genomic-scores').nth(1)).toContainText(mpc);
    await expect(page.locator('gpf-genomic-scores').nth(2)).toContainText(clndn);
  });

  test('should remove histogram from histograms list', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const dbSNP = 'dbSNP_RS - dbSNP ID (i.e. rs number)';

    const gnomad_genomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${dbSNP}")`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomad_genomes}")`).click();


    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);

    await page.locator('gpf-remove-button').nth(2).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(gnomad_genomes);
    await expect(page.locator('gpf-genomic-scores').nth(1)).toContainText(dbSNP);

    await page.locator('gpf-remove-button').nth(0).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(1);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(dbSNP);

    await page.locator('gpf-remove-button').nth(0).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(0);
  });

  test('should check if dropdown options are filtered when selecting histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const dbSNP = 'dbSNP_RS - dbSNP ID (i.e. rs number)';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(6);
    await page.locator(`mat-option:has-text("${clndn}")`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(5);
    await expect(page.locator(`mat-option:has-text("${clndn}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${dbSNP}")`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(4);
    await expect(page.locator(`mat-option:has-text("${dbSNP}")`)).not.toBeVisible();
  });

  test('should check if error message is shown when too many categorical values are selected', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();

    await expect(page.locator('gpf-categorical-histogram')).toBeVisible();
    await expect(page.getByText(clndn)).toBeVisible();

    await expect(page.locator('gpf-categorical-histogram svg')).toBeVisible();
    // await expect(page.locator('gpf-categorical-histogram svg')).toContainText('166066 values');
    await expect(page.locator('gpf-genomic-scores gpf-errors-alert')).toBeVisible();
    await expect(page.locator('gpf-genomic-scores gpf-errors-alert')).toHaveText('Please select less than 1000 values.');
    // expect buttons to be disabled
  });

  test('should share and load query with categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await page.locator('rect[id="Conflicting_classifications_of_pathogenicity"]').click();
    await page.locator('rect[id="Likely_pathogenic"]').click();
    await page.locator('rect[id="Benign/Likely_benign"]').click();

    // await page.waitForSelector('gpf-errors-alert', {state: 'detached'});
    await expect(page.locator('gpf-genomic-scores-block').getByText('3 values')).toBeVisible();
    await expect(page.locator('gpf-errors-alert').filter({ hasText: 'Please select at least one' })).not.toBeVisible();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('rect[id="Conflicting_classifications_of_pathogenicity"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="Likely_pathogenic"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="Benign/Likely_benign"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
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