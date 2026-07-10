import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { scanCSV } from 'nodejs-polars';
import { GenotypeBrowserPage } from './pages/genotype-browser.page';

test.describe('Genomic scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test.use({viewport: { width: 1920, height: 2160 }});

  test('should display genomic scores panel after selecting score ' +
  'and remove it after "remove filter" button click', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    await expect(genomicScores.scores).toBeHidden();

    await genomicScores.openScoreDropdown();
    await genomicScores.matOptions.nth(0).click();

    await expect(genomicScores.scores).toBeVisible();

    await genomicScores.removeButton.click();
    await expect(genomicScores.scores).toBeHidden();
  });

  test('should enter filter data and check how it affects the histogram', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const exomeGnomadScore = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';

    await genomicScores.selectScore(exomeGnomadScore);

    await genomicScores.fromInputs.nth(0).clear();
    await genomicScores.fromInputs.nth(0).pressSequentially('0.063');
    await expect(genomicScores.partitionsText.nth(0)).toHaveText('~74244341 (97.47%)');

    await genomicScores.toInputs.nth(0).clear();
    await genomicScores.toInputs.nth(0).pressSequentially('1.096');
    await expect(genomicScores.partitionsText.nth(1)).toHaveText('~840182 (1.10%)');
    await expect(genomicScores.partitionsText.nth(2)).toHaveText('~1090009 (1.43%)');

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
      'A deleteriousness prediction score for missense variants';

    await genomicScores.selectScore(mpcScore);

    await genomicScores.fromInputs.nth(0).clear();
    await genomicScores.fromInputs.nth(0).pressSequentially('0.3');
    await expect(genomicScores.partitionsText.nth(0)).toHaveText('~21727789 (32.46%)');

    await genomicScores.toInputs.nth(0).clear();
    await genomicScores.toInputs.nth(0).pressSequentially('1.45');
    await expect(genomicScores.partitionsText.nth(1)).toHaveText('~9402408 (14.05%)');
    await expect(genomicScores.partitionsText.nth(2)).toHaveText('~35798106 (53.49%)');

    await genomicScores.removeButton.nth(0).click();
    await expect(genomicScores.partitionsText.nth(0)).toHaveText('~74244341 (97.47%)');
    await expect(genomicScores.partitionsText.nth(1)).toHaveText('~840182 (1.10%)');
    await expect(genomicScores.partitionsText.nth(2)).toHaveText('~1090009 (1.43%)');
  });

  test('should select categorical histogram', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await genomicScores.selectScore(clinsig);
    await expect(genomicScores.scores).toBeVisible();
    await expect(genomicScores.helperModal).toBeVisible();
    await expect(genomicScores.categoricalValuesDropdown).toBeVisible();
    await expect(genomicScores.categoricalRemoveButton).toBeVisible();
  });

  test('should check histograms order when adding new histogram', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    const gnomad_exomes = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';

    await genomicScores.selectScore(clndn);
    await genomicScores.selectScore(mpc);
    await genomicScores.selectScore(gnomad_exomes);

    await expect(genomicScores.scores).toHaveCount(3);
    await expect(genomicScores.score(0)).toContainText(gnomad_exomes);
    await expect(genomicScores.score(1)).toContainText(mpc);
    await expect(genomicScores.score(2)).toContainText(clndn);
  });

  test('should remove histogram from histograms list', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    const gnomad_genomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';

    await genomicScores.selectScore(clndn);
    await genomicScores.selectScore(mpc);
    await genomicScores.selectScore(gnomad_genomes);


    await expect(genomicScores.scores).toHaveCount(3);

    await genomicScores.categoricalRemoveButton.nth(2).click();
    await expect(genomicScores.scores).toHaveCount(2);
    await expect(genomicScores.score(0)).toContainText(gnomad_genomes);
    await expect(genomicScores.score(1)).toContainText(mpc);

    await genomicScores.categoricalRemoveButton.nth(0).click();
    await expect(genomicScores.scores).toHaveCount(1);
    await expect(genomicScores.score(0)).toContainText(mpc);

    await genomicScores.categoricalRemoveButton.nth(0).click();
    await expect(genomicScores.scores).toHaveCount(0);
  });

  test('should check if dropdown options are filtered when selecting histogram', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    const mpc = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    await genomicScores.openScoreDropdown();
    await expect(genomicScores.matOptions).toHaveCount(5);
    await genomicScores.scoreOption(clndn).click();

    await genomicScores.openScoreDropdown();
    await expect(genomicScores.matOptions).toHaveCount(4);
    await expect(genomicScores.scoreOptionRow(clndn)).not.toBeVisible();
    await genomicScores.scoreOption(mpc).click();

    await genomicScores.openScoreDropdown();
    await expect(genomicScores.matOptions).toHaveCount(3);
    await expect(genomicScores.scoreOptionRow(mpc)).not.toBeVisible();
  });

  test('should check error message is shown when no categorical values are selected', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);

    await expect(genomicScores.categoricalValuesDropdown).toBeVisible();
    await expect(page.getByText(clndn)).toBeVisible();

    await expect(genomicScores.errorsAlert).toBeVisible();
    await expect(genomicScores.errorsAlert).toHaveText('Please select at least one value.');
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('should share query with categorical histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await genomicScores.selectScore(clinsig);

    await genomicScores.searchBox.focus();
    await page.keyboard.type('Conflicting_classifications_of_pathogenicity');
    const conflicting = genomicScores.valueOption(/^Conflicting_classifications_of_pathogenicity \(/);
    await expect(conflicting).toHaveCount(1);
    await conflicting.click();
    await genomicScores.searchBox.focus();
    await page.keyboard.type('Likely_pathogenic');
    const likelyPath = genomicScores.valueOption(/^Likely_pathogenic \(/);
    await expect(likelyPath).toHaveCount(1);
    await likelyPath.click();
    await genomicScores.searchBox.focus();
    await page.keyboard.type('Benign/Likely_benign');
    const benign = genomicScores.valueOption(/^Benign\/Likely_benign \(/);
    await expect(benign).toHaveCount(1);
    await benign.click();

    await expect(genomicScores.valueWrapper).toHaveCount(3);
    await expect(genomicScores.errorsAlertContaining('Please select at least one')).not.toBeVisible();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genomicScores.valueWrapper).toHaveCount(3);
    await expect(genomicScores.errorsAlertContaining('Please select at least one')).not.toBeVisible();
    await expect(genomicScores.valuesList.getByText(/Conflicting_classifications_of_pathogenicity/)).toBeVisible();
    await expect(genomicScores.valuesList.getByText(/Likely_pathogenic \(/)).toBeVisible();
    await expect(genomicScores.valuesList.getByText(/Benign\/Likely_benign \(/)).toBeVisible();
  });

  test('should check table result when filtering with categorical histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await genomicScores.selectScore(clinsig);

    await genomicScores.searchBox.focus();
    await page.keyboard.type('Pathogenic/Likely_pathogenic');
    await genomicScores.valueOptionByText('Pathogenic/Likely_pathogenic (27651)').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('1 variant selected', { timeout: 120000 });
  });


  test('should download with categorical histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);

    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('not_provided');
    const notProvidedDownload = genomicScores.valueOption(/^not_provided \(/);
    await expect(notProvidedDownload).toHaveCount(1);
    await notProvidedDownload.click();

    await page.locator('gpf-effect-types').getByText('All').click();

    const downloadPromise = page.waitForEvent('download');
    await genotypeBrowser.downloadButton.click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/genomic-scores/variants-1.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('should check genomic scores order and dropdown content', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';
    await genomicScores.selectScore(clndn);

    await expect(genomicScores.scores).toHaveCount(1);
    await expect(genomicScores.scoreTitles).toHaveText(clndn);

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await genomicScores.openScoreDropdown();
    await expect(genomicScores.scoreOptionRow(clndn)).not.toBeVisible();
    await genomicScores.scoreOption(clinsig).click();

    await expect(genomicScores.scores).toHaveCount(2);
    await expect(genomicScores.scoreTitles.nth(0)).toHaveText(clinsig);
    await expect(genomicScores.scoreTitles.nth(1)).toHaveText(clndn);

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await genomicScores.openScoreDropdown();
    await expect(genomicScores.scoreOptionRow(clndn)).not.toBeVisible();
    await expect(genomicScores.scoreOptionRow(clinsig)).not.toBeVisible();
    await genomicScores.scoreOption(gnomadGenomes).click();

    await expect(genomicScores.scores).toHaveCount(3);
    await expect(genomicScores.scoreTitles.nth(0)).toHaveText(gnomadGenomes);
    await expect(genomicScores.scoreTitles.nth(1)).toHaveText(clinsig);
    await expect(genomicScores.scoreTitles.nth(2)).toHaveText(clndn);
  });

  test('should remove genomic score from scores list and check dropdown content', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const exomeGnomadScore = 'gnomad_4_1_exomes_af_percent - Alternate allele frequency as percent';
    await genomicScores.selectScore(exomeGnomadScore);

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await genomicScores.selectScore(clinsig);

    const gnomadGenomes = 'gnomad_4_1_genomes_af_percent - Alternate allele frequency as percent';
    await genomicScores.selectScore(gnomadGenomes);

    await expect(genomicScores.scores).toHaveCount(3);

    await genomicScores.removeButton.nth(1).click();
    await expect(genomicScores.scores).toHaveCount(2);
    await expect(genomicScores.scoreTitles.nth(0)).toHaveText(gnomadGenomes);
    await expect(genomicScores.scoreTitles.nth(1)).toHaveText(exomeGnomadScore);
    await genomicScores.openScoreDropdown();
    await expect(genomicScores.scoreOption(clinsig)).toBeVisible();
  });


  test('should check clinsig "Other values" bar is not available in dropdown', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';
    await genomicScores.selectScore(clinsig);

    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('Other values');
    await expect(genomicScores.valuesSuggestionsDropdown).not.toBeVisible();
  });

  test('should check downloded file filtering with genomic scores in phenotype tool', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');

    await page.locator('gpf-pheno-measure-selector #search-box').click();
    await page.getByText('instrument_1.measure_1').first().click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);

    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('not_provided');
    const notProvidedPheno = genomicScores.valueOption(/^not_provided \(/);
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
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');

    await page.locator('gpf-pheno-measure-selector #search-box').click();
    await page.getByText('instrument_1.measure_1').first().click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);

    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('not_provided');
    const notProvidedLoaded = genomicScores.valueOption(/^not_provided \(/);
    await expect(notProvidedLoaded).toHaveCount(1);
    await notProvidedLoaded.click();
    await genomicScores.categoricalSearchBox.focus();
    await page.keyboard.type('Primary_ciliary_dyskinesia');
    const primaryCiliary = genomicScores.valueOption(/^Primary_ciliary_dyskinesia \(/);
    await expect(primaryCiliary).toHaveCount(1);
    await primaryCiliary.click();

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await expect(genomicScores.valuesList.getByText(/not_provided \(/)).toBeVisible();
    await expect(genomicScores.valuesList.getByText(/Primary_ciliary_dyskinesia \(/)).toBeVisible();
  });

  test('should filter by multiple genomic scores', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    await page.locator('gpf-effect-types').getByText('All').click();

    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);

    await genomicScores.scoreSearchBox(0).focus();
    await page.keyboard.type('not_provided');
    const notProvided = genomicScores.valueOption(/^not_provided \(/);
    await expect(notProvided).toHaveCount(1);
    await notProvided.click();
    await genomicScores.scoreSearchBox(0).focus();
    await page.keyboard.type('not_specified');
    const notSpecified = genomicScores.valueOption(/^not_specified \(/);
    await expect(notSpecified).toHaveCount(1);
    await notSpecified.click();
    await genomicScores.scoreSearchBox(0).focus();
    await page.keyboard.type('Inborn_genetic_diseases');
    const inbornGenetic = genomicScores.valueOption(/^Inborn_genetic_diseases \(/);
    await expect(inbornGenetic).toHaveCount(1);
    await inbornGenetic.click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('7 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await genomicScores.selectScore(clinsig);

    await genomicScores.scoreSearchBox(0).focus();
    await page.keyboard.type('Uncertain_significance');
    const uncertainSig = genomicScores.valueOption(/^Uncertain_significance \(/);
    await expect(uncertainSig).toHaveCount(1);
    await uncertainSig.click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('3 variants selected', { timeout: 120000 });

    await genomicScores.removeButton.nth(1).click();
    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('5 variants selected', { timeout: 120000 });
  });

  test('should filter by genomic categorical score and gene categorical score', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    const categoricalHistogram = genotypeBrowser.genes.geneScores.categorical;
    await page.locator('gpf-effect-types').getByText('All').click();

    await genotypeBrowser.genes.openGeneScores();
    await genotypeBrowser.genes.geneScores.selectScore(
      'SFARI Gene Score - Evidence strength supporting a gene\'s association with autism'
    );

    await categoricalHistogram.selectMode('click selector');
    await categoricalHistogram.bar('1').click();
    await categoricalHistogram.bar('2').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('26 variants selected', { timeout: 120000 });

    const clinsig = 'CLNSIG - Aggregate germline classification for this single variant;' +
    ' multiple values are separated by a vertical bar';

    await genomicScores.selectScore(clinsig);

    await genomicScores.searchBox.focus();
    await page.keyboard.type('Pathogenic');
    await genomicScores.valueOptionByText('Pathogenic (158261)').click();

    await genomicScores.searchBox.focus();
    await page.keyboard.type('Uncertain_significance');
    await genomicScores.valueOptionByText('Uncertain_significance (1363638)').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('7 variants selected', { timeout: 120000 });

    const shareLinkUrl = await genotypeBrowser.getShareLink();
    await expect(genotypeBrowser.saveQueryDropdown).toBeVisible();
    await page.goto(shareLinkUrl, {waitUntil: 'load'});

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('7 variants selected', { timeout: 120000 });
  });

  test('should open measure description modal', async({ page }) => {
    const genomicScores = new GenotypeBrowserPage(page).genomicScores;
    const clndn = 'CLNDN - ClinVar\'s preferred disease name for' +
    ' the concept specified by disease identifiers in CLNDISDB';

    await genomicScores.selectScore(clndn);
    await genomicScores.helpIcon.click();
    await expect(genomicScores.descriptionModal).toBeVisible();
    await expect(genomicScores.descriptionModal).toContainText('CLNDN');
    await expect(genomicScores.descriptionModal.locator('img')).toBeVisible();

    await genomicScores.closeButton.click();
    await expect(genomicScores.descriptionModal).not.toBeVisible();
  });

  test('should download with continuous histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const genomicScores = genotypeBrowser.genomicScores;
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');

    // MPC only annotates missense variants; the default Effect Types
    // selection is LGDs-only (no missense). Click All so the MPC range
    // filter has a non-empty result set deterministically on Jenkins.
    await page.locator('gpf-effect-types').getByRole('button', {name: 'All'}).click();

    const mpcScore = 'mpc - Missense badness, PolyPhen-2, and Constraint. ' +
    'A deleteriousness prediction score for missense variants';

    await genomicScores.selectScore(mpcScore);

    await genomicScores.fromInputs.clear();
    await genomicScores.fromInputs.pressSequentially('0.2');

    await genomicScores.toInputs.clear();
    await genomicScores.toInputs.pressSequentially('3.95');

    const downloadPromise = page.waitForEvent('download');
    await genotypeBrowser.downloadButton.click();
    const download = await downloadPromise;

    const fixtureData = scanCSV(await download.path(), {sep: '\t'});
    const downloadData = scanCSV('fixtures/genomic-scores/variants.tsv', {sep: '\t'});
    const fixtureFrame = (await fixtureData.collect()).sort('family id');
    const downloadFrame = (await downloadData.collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});
