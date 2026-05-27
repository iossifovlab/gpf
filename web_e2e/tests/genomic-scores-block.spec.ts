import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';

test.describe('Genomic scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test.use({viewport: { width: 1920, height: 2160 }});

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
    await page.locator(`mat-option:has-text("${exomeGnomadScore}") span`).click();

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
    await page.locator(`mat-option:has-text("${mpcScore}") span`).click();

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
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();
    await expect(page.locator('gpf-genomic-scores')).toBeVisible();
    await expect(page.locator('gpf-helper-modal')).toBeVisible();
    await expect(page.locator('gpf-categorical-values-dropdown')).toBeVisible();
    await expect(page.locator('gpf-remove-button')).toBeVisible();
  });

  test('should check histograms order when adding new histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    const gnomad_exomes = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpc}") span`).click();
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomad_exomes}") span`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(gnomad_exomes);
    await expect(page.locator('gpf-genomic-scores').nth(1)).toContainText(mpc);
    await expect(page.locator('gpf-genomic-scores').nth(2)).toContainText(clndn);
  });

  test('should remove histogram from histograms list', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    const gnomad_genomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpc}") span`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomad_genomes}") span`).click();


    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);

    await page.locator('gpf-remove-button').nth(2).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(gnomad_genomes);
    await expect(page.locator('gpf-genomic-scores').nth(1)).toContainText(mpc);

    await page.locator('gpf-remove-button').nth(0).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(1);
    await expect(page.locator('gpf-genomic-scores').nth(0)).toContainText(mpc);

    await page.locator('gpf-remove-button').nth(0).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(0);
  });

  test('should check if dropdown options are filtered when selecting histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(5);
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(4);
    await expect(page.locator(`mat-option:has-text("${clndn}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${mpc}") span`).click();

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator('mat-option')).toHaveCount(3);
    await expect(page.locator(`mat-option:has-text("${mpc}")`)).not.toBeVisible();
  });

  test('should check error message is shown when no categorical values are selected', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await expect(page.locator('gpf-categorical-values-dropdown')).toBeVisible();
    await expect(page.getByText(clndn)).toBeVisible();

    await expect(page.locator('gpf-genomic-scores').locator('gpf-errors-alert')).toBeVisible();
    await expect(page.locator('gpf-genomic-scores gpf-errors-alert'))
      .toHaveText('Please select at least one value.');
    await expect(page.getByRole('button', {name: 'Table Preview'})).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Share/save query'})).toBeDisabled();
    await expect(page.getByRole('button', {name: 'Download'})).toBeDisabled();
  });

  test('should share query with categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('Conflicting_classifications_of_pathogenicity');
    const conflicting = page.locator('mat-option > span > span').filter({hasText: /^Conflicting_classifications_of_pathogenicity \(/});
    await expect(conflicting).toHaveCount(1);
    await conflicting.click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('Likely_pathogenic');
    const likelyPath = page.locator('mat-option > span > span').filter({hasText: /^Likely_pathogenic \(/});
    await expect(likelyPath).toHaveCount(1);
    await likelyPath.click();
    await page.locator('#search-box').focus();
    await page.keyboard.type('Benign/Likely_benign');
    const benign = page.locator('mat-option > span > span').filter({hasText: /^Benign\/Likely_benign \(/});
    await expect(benign).toHaveCount(1);
    await benign.click();

    await expect(page.locator('.value-wrapper')).toHaveCount(3);
    await expect(page.locator('gpf-errors-alert').filter({ hasText: 'Please select at least one' })).not.toBeVisible();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('.value-wrapper')).toHaveCount(3);
    await expect(page.locator('gpf-errors-alert').filter({ hasText: 'Please select at least one' })).not.toBeVisible();
    await expect(page.locator('#values-list').getByText(/Conflicting_classifications_of_pathogenicity/)).toBeVisible();
    await expect(page.locator('#values-list').getByText(/Likely_pathogenic \(/)).toBeVisible();
    await expect(page.locator('#values-list').getByText(/Benign\/Likely_benign \(/)).toBeVisible();
  });

  test('should check table result when filtering with categorical histogram', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('Pathogenic/Likely_pathogenic');
    await page.locator('mat-option:has-text("Pathogenic/Likely_pathogenic (27651)") > span > span').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('1 variant selected', { timeout: 120000 });
  });


  test('should download with categorical histogram', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-categorical-values-dropdown #search-box').focus();
    await page.keyboard.type('not_provided');
    const notProvidedDownload = page.locator('mat-option > span > span').filter({hasText: /^not_provided \(/});
    await expect(notProvidedDownload).toHaveCount(1);
    await notProvidedDownload.click();

    await page.locator('gpf-effect-types').getByText('All').click();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/genomic-scores/variants-1.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check genomic scores order and dropdown content', async({ page }) => {
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(1);
    await expect(page.locator('gpf-genomic-scores .title-wrapper')).toHaveText(clndn);

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${clndn}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(clinsig);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(clndn);

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${clndn}")`)).not.toBeVisible();
    await expect(page.locator(`mat-option:has-text("${clinsig}")`)).not.toBeVisible();
    await page.locator(`mat-option:has-text("${gnomadGenomes}") span`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(gnomadGenomes);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(clinsig);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(2)).toHaveText(clndn);
  });

  test('should remove genomic score from scores list and check dropdown content', async({ page }) => {
    const exomeGnomadScore = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${exomeGnomadScore}") span`).click();

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${gnomadGenomes}") span`).click();

    await expect(page.locator('gpf-genomic-scores')).toHaveCount(3);

    await page.locator('#remove-button').nth(1).click();
    await expect(page.locator('gpf-genomic-scores')).toHaveCount(2);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(0)).toHaveText(gnomadGenomes);
    await expect(page.locator('gpf-genomic-scores .title-wrapper').nth(1)).toHaveText(exomeGnomadScore);
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await expect(page.locator(`mat-option:has-text("${clinsig}") span`)).toBeVisible();
  });


  test('should check clinsig "Other values" bar is not available in dropdown', async({ page }) => {
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

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
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-categorical-values-dropdown #search-box').focus();
    await page.keyboard.type('not_provided');
    const notProvidedPheno = page.locator('mat-option > span > span').filter({hasText: /^not_provided \(/});
    await expect(notProvidedPheno).toHaveCount(1);
    await notProvidedPheno.click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await page.getByText('Download').click();
    const download = await downloadPromise;
    const downloadData = scanCSV(await download.path(), {nullValues: '-'});
    const fixtureData = scanCSV('fixtures/genomic-scores/pheno-report.csv', {nullValues: '-'});
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
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-categorical-values-dropdown #search-box').focus();
    await page.keyboard.type('not_provided');
    const notProvidedLoaded = page.locator('mat-option > span > span').filter({hasText: /^not_provided \(/});
    await expect(notProvidedLoaded).toHaveCount(1);
    await notProvidedLoaded.click();
    await page.locator('gpf-categorical-values-dropdown #search-box').focus();
    await page.keyboard.type('Primary_ciliary_dyskinesia');
    const primaryCiliary = page.locator('mat-option > span > span').filter({hasText: /^Primary_ciliary_dyskinesia \(/});
    await expect(primaryCiliary).toHaveCount(1);
    await primaryCiliary.click();

    await page.getByRole('button', {name: 'Share/save query'}).click();
    await expect(page.locator('#save-query-dropdown')).toBeVisible();
    const shareLinkUrl = await page.locator('#link-input').inputValue();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(page.locator('#values-list').getByText(/not_provided \(/)).toBeVisible();
    await expect(page.locator('#values-list').getByText(/Primary_ciliary_dyskinesia \(/)).toBeVisible();
  });

  test('should filter by multiple genomic scores', async({ page }) => {
    await page.locator('gpf-effect-types').getByText('All').click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clndn}") span`).click();

    await page.locator('gpf-genomic-scores').nth(0).locator('#search-box').focus();
    await page.keyboard.type('not_provided');
    const notProvided = page.locator('mat-option > span > span').filter({hasText: /^not_provided \(/});
    await expect(notProvided).toHaveCount(1);
    await notProvided.click();
    await page.locator('gpf-genomic-scores').nth(0).locator('#search-box').focus();
    await page.keyboard.type('not_specified');
    const notSpecified = page.locator('mat-option > span > span').filter({hasText: /^not_specified \(/});
    await expect(notSpecified).toHaveCount(1);
    await notSpecified.click();
    await page.locator('gpf-genomic-scores').nth(0).locator('#search-box').focus();
    await page.keyboard.type('Inborn_genetic_diseases');
    const inbornGenetic = page.locator('mat-option > span > span').filter({hasText: /^Inborn_genetic_diseases \(/});
    await expect(inbornGenetic).toHaveCount(1);
    await inbornGenetic.click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('7 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    await page.locator('gpf-genomic-scores').nth(0).locator('#search-box').focus();
    await page.keyboard.type('Uncertain_significance');
    const uncertainSig = page.locator('mat-option > span > span').filter({hasText: /^Uncertain_significance \(/});
    await expect(uncertainSig).toHaveCount(1);
    await uncertainSig.click();

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
      .selectOption('SFARI Gene Score - Evidence strength supporting a gene\'s association with autism');

    await page.getByRole('button', {name: 'Mode'}).click();
    await page.getByRole('menuitem', {name: 'click selector'}).click();
    await page.locator('rect[id="1"]').click();
    await page.locator('rect[id="2"]').click();

    await page.getByRole('button', {name: 'Table Preview'}).click();
    await expect(page.locator('#variants-count-span > span')).toHaveText('26 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${clinsig}") span`).click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('Pathogenic');
    await page.locator('mat-option:has-text("Pathogenic (158261)") > span > span').click();

    await page.locator('#search-box').focus();
    await page.keyboard.type('Uncertain_significance');
    await page.locator('mat-option:has-text("Uncertain_significance (1363638)")  > span > span').click();

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
    await page.locator(`mat-option:has-text("${clndn}") span`).click();
    await page.locator('gpf-genomic-scores-block >> #help-icon').click();
    await expect(page.locator('.modal-content')).toBeVisible();
    await expect(page.locator('.modal-content')).toContainText('CLNDN');
    await expect(page.locator('.modal-content').locator('img')).toBeVisible();

    await page.locator('.modal-content').locator('#close-button').click();
    await expect(page.locator('.modal-content')).not.toBeVisible();
  });

  test('should download with continuous histogram', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');

    // MPC only annotates missense variants; the default Effect Types
    // selection is LGDs-only (no missense). Click All so the MPC range
    // filter has a non-empty result set deterministically on Jenkins.
    await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    await page.locator('gpf-genomic-scores-block >> mat-form-field').click();
    await page.locator(`mat-option:has-text("${mpcScore}") span`).click();

    await page.locator('input#from-input-field').clear();
    await page.locator('input#from-input-field').pressSequentially('0.2');

    await page.locator('input#to-input-field').clear();
    await page.locator('input#to-input-field').pressSequentially('3.95');

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/genomic-scores/variants.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});
