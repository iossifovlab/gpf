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
    await page.locator('input#from-input-field').nth(0).pressSequentially('0.063');
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~74244341 (97.47%)');

    await page.locator('input#to-input-field').nth(0).clear();
    await page.locator('input#to-input-field').nth(0).pressSequentially('1.096');
    await expect(page.locator('text.partitions-text').nth(1)).toHaveText('~840182 (1.10%)');
    await expect(page.locator('text.partitions-text').nth(2)).toHaveText('~1090009 (1.43%)');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
      'A deleteriousness prediction score for missense variants';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}")`).click();

    await page.locator('input#from-input-field').nth(0).clear();
    await page.locator('input#from-input-field').nth(0).pressSequentially('0.3');
    await expect(page.locator('text.partitions-text').nth(0)).toHaveText('~21727789 (32.46%)');

    await page.locator('input#to-input-field').nth(0).clear();
    await page.locator('input#to-input-field').nth(0).pressSequentially('1.45');
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

    await expect(page.locator('gpf-categorical-histogram svg')).toContainText('166066 values');
    await expect(page.locator('gpf-genomic-scores').locator('gpf-errors-alert')).toBeVisible();
    await expect(page.locator('gpf-genomic-scores gpf-errors-alert'))
      .toHaveText('Please select less than 1000 values.');
    await expect(page.getByRole('button', {name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();
  });

  test('should share query with categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await page.locator('rect[id="Conflicting_classifications_of_pathogenicity"]').click();
    await page.locator('rect[id="Likely_pathogenic"]').click();
    await page.locator('rect[id="Benign/Likely_benign"]').click();

    await expect(page.locator('gpf-genomic-scores-block').getByText('3 values')).toBeVisible();
    await expect(page.locator('gpf-errors-alert').filter({ hasText: 'Please select at least one' })).not.toBeVisible();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('gpf-genomic-scores-block').getByText('3 values')).toBeVisible();
    await expect(page.locator('gpf-errors-alert').filter({ hasText: 'Please select at least one' })).not.toBeVisible();
    await expect(page.locator('rect[id="Conflicting_classifications_of_pathogenicity"]'))
      .toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="Likely_pathogenic"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="Benign/Likely_benign"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should check table result when filtering with categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('Pathogenic/Likely_pathogenic');
    await page.locator('mat-option:has-text("Pathogenic/Likely_pathogenic (27651)")').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('1 variant selected', { timeout: 120000 });
  });


  test('should download with categorical histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();

    await page.locator('[gpf-histogram-range-selector-line]').nth(0).hover();
    await page.mouse.down();
    await page.mouse.move(700, 400, {steps: 3});
    await page.mouse.up();

    await page.locator('[gpf-histogram-range-selector-line]').nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(900, 400, {steps: 3});
    await page.mouse.up();

    await page.locator('gpf-effect-types').getByText('All').click();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('playwright/fixtures/genomic-scores/variants-1.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check genomic scores order and dropdown content', async({ page }) => {
    const dbSNP = 'dbSNP_RS - dbSNP ID (i.e. rs number)';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${dbSNP}")`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(1);
    await expect(page.locator('gpf-genomic-scores .title-wrapper')).toHaveText(dbSNP);

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${dbSNP}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(clinsig);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(dbSNP);

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${dbSNP}")`)).not.toBeVisible();
    await expect(page.locator(`mat-option:has-text("${clinsig}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${gnomadGenomes}")`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(gnomadGenomes);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(clinsig);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(2)).toHaveText(dbSNP);
  });

  test('should remove genomic score from scores list and check dropdown content', async({ page }) => {
    const dbSNP = 'dbSNP_RS - dbSNP ID (i.e. rs number)';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${dbSNP}")`).click();

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomadGenomes}")`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);

    await page.locator('#remove-button').nth(1).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(gnomadGenomes);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(dbSNP);
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${clinsig}")`)).toBeVisible();
  });

  test('should check clndn histogram other bar and values count', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();

    await expect(page.locator('gpf-categorical-histogram')).toBeVisible();
    await expect(page.getByText(clndn)).toBeVisible();

    await expect(page.locator('gpf-categorical-histogram svg')).toContainText('166066 values');
    await page.locator('[gpf-histogram-range-selector-line]').nth(1).hover();
    await page.mouse.down();
    await page.mouse.move(1200, 400, {steps: 3});
    await page.mouse.up();

    await expect(page.locator('gpf-categorical-histogram svg')).toContainText('10 values');
    await expect(page.locator('rect[id="Other values"]')).toHaveCSS('fill', 'rgb(176, 196, 222)');
  });

  test('should check clinsig histogram bars count', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await expect(page.locator('gpf-genomic-scores').locator('rect[style*="fill: steelblue"]')).toHaveCount(21);
    await expect(
      page.locator('gpf-genomic-scores').locator('rect[style*="fill: steelblue"]').nth(20)
    ).toHaveId('Other values');
  });

  test('should check clinsig histogram other bar in other modes', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click();

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();

    await expect(
      page.locator('gpf-genomic-scores').locator('rect[style*="fill: lightsteelblue"]').nth(20)
    ).toHaveId('Other values');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click();
    await page.locator('gpf-categorical-values-dropdown #search-box').focus();
    await page.keyboard.type('Other values');
    await expect(page.locator('.values-suggestions-dropdown')).not.toBeVisible();
  });

  test('should check downloded file filtering with genomic scores in phenotype tool', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');

    await page.locator('gpf-pheno-measure-selector #search-box').click();
    await page.getByText('instrument_1.measure_1').first().click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="not_provided"]').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByText('Download').click();
    const download = await downloadPromise;
    const downloadData = scanCSV(await download.path(), {nullValues: '-'});
    const fixtureData = scanCSV('playwright/fixtures/genomic-scores/pheno-report.csv', {nullValues: '-'});
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check loaded query filtering with genomic scores in phenotype tool', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');

    await page.locator('gpf-pheno-measure-selector #search-box').click();
    await page.getByText('instrument_1.measure_1').first().click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="not_provided"]').click();
    await page.locator('rect[id="Primary_ciliary_dyskinesia"]').click();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('rect[id="not_provided"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
    await expect(page.locator('rect[id="Primary_ciliary_dyskinesia"]')).toHaveCSS('fill', 'rgb(70, 130, 180)');
  });

  test('should filter by multiple genomic scores', async({ page }) => {
    await page.locator('gpf-effect-types').getByText('All').click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();
    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="not_provided"]').click();
    await page.locator('rect[id="not_specified"]').click();
    await page.locator('rect[id="Inborn_genetic_diseases"]').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('7 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click({force: true});
    await page.getByRole('button', {name: 'Mode'}).nth(0).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="Uncertain_significance"]').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('3 variants selected', { timeout: 120000 });

    await page.locator('#remove-button').nth(1).click();
    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('5 variants selected', { timeout: 120000 });
  });

  test('should filter by genomic categorical score and gene categorical score', async({ page }) => {
    await page.locator('gpf-effect-types').getByText('All').click();

    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
      .selectOption('gene-score - Evidence strength supporting a gene\'s association with autism');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="1"]').click();
    await page.locator('rect[id="2"]').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('26 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}")`).click({ force: true });
    await page.getByRole('button', {name: 'Mode'}).nth(1).click();
    await page.getByRole('menuitem', {name: 'dropdown selector'}).click({force: true});
    await page.locator('#search-box').focus();
    await page.keyboard.type('Pathogenic');
    await page.locator('mat-option:has-text("Pathogenic (158261)")').click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('Uncertain_significance');
    await page.locator('mat-option:has-text("Uncertain_significance (1363638)")').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('7 variants selected', { timeout: 120000 });

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('7 variants selected', { timeout: 120000 });
  });

  test('should open measure description modal', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}")`).click();
    await page.locator('gpf-genomic-scores-block >> #help-icon').click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('.modal-content')).toContainText('CLNDN');
    await expect(page.locator('.modal-content').locator('img')).toBeVisible();

    await page.locator('.modal-content').locator('#close-button').click();
    await expect(page.locator('.modal-content')).not.toBeVisible();
  });

  test('should download with continuous histogram', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}")`).click();

    await page.locator('input#from-input-field').clear();
    await page.locator('input#from-input-field').pressSequentially('1.25');

    await page.locator('input#to-input-field').clear();
    await page.locator('input#to-input-field').pressSequentially('1.8');

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