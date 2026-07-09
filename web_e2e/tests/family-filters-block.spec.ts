import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { datasetIds } from './utils';
import { scanCSV } from 'nodejs-polars';
import { GenotypeBrowserPage } from './pages/genotype-browser.page';
import { PersonFilters } from './components/person-filters.component';

test.describe('Family filters block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('should display family ids panel', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.familyFilters.familyIdsPanel).not.toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyIds();
    await expect(genotypeBrowser.familyFilters.familyIdsPanel).toBeVisible();
  });

  test('should display error alert in family ids panel when the textarea is empty', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await genotypeBrowser.familyFilters.openFamilyIds();
    await expect(genotypeBrowser.familyFilters.familyIds.emptyHint).toBeVisible();

    await genotypeBrowser.familyFilters.familyIds.textarea.pressSequentially('f1');
    await expect(genotypeBrowser.familyFilters.familyIds.emptyHint).not.toBeVisible();

    await genotypeBrowser.familyFilters.familyIds.clear();
    await expect(genotypeBrowser.familyFilters.familyIds.emptyHint).toBeVisible();
  });

  test('should test save/share query after entering family ids', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyIdsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyIdsTab();

    await genotypeBrowser.familyFilters.familyIds.type('14338');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('1 variant selected');

    await genotypeBrowser.saveQueryDropdownButton.click();
    await expect(genotypeBrowser.linkInput).not.toHaveValue('');
    const url = await genotypeBrowser.linkInput.inputValue();
    await page.goto(url);

    await expect(genotypeBrowser.familyFilters.familyIds.textarea).toHaveText('14338');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('1 variant selected');
  });

  test('should test resetting family ids state', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyIdsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyIdsTab();

    await genotypeBrowser.familyFilters.familyIds.type('f1, f2');

    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    await genotypeBrowser.familyFilters.openAllTab();

    await genotypeBrowser.familyFilters.openFamilyIdsTab();
    await expect(genotypeBrowser.familyFilters.familyIds.textarea).toBeEmpty();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('should test family ids error state is reset when switching tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyIdsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyIdsTab();

    await expect(genotypeBrowser.familyFilters.familyIds.emptyHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.familyFilters.openAllTab();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('should check number of selected variants when changing list of ids and if table is reset', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyIdsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyIdsTab();

    await genotypeBrowser.familyFilters.familyIds.type('f5');

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('2 variants selected');

    await genotypeBrowser.familyFilters.familyIds.type(', f7');
    await expect(genotypeBrowser.previewTable).not.toBeVisible();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('3 variants selected');
  });

  test('should preview table and download filtered by Family Tags', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyTagsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyTagsTab();

    await expect(genotypeBrowser.familyFilters.familyTags.root).toBeVisible();

    await genotypeBrowser.familyFilters.familyTags.addTag('nuclear_family');
    await genotypeBrowser.familyFilters.familyTags.removeTag('quad_family');

    await genotypeBrowser.tablePreviewButtonId.click();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('15 variants selected', { timeout: 120000 });


    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButtonId.click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(
      'fixtures/genotype-browser/variants-2.tsv',
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
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyTagsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyTagsTab();

    await expect(genotypeBrowser.familyFilters.familyTags.root).toBeVisible();

    await genotypeBrowser.familyFilters.familyTags.toggleOr();

    await genotypeBrowser.familyFilters.familyTags.removeTag('nuclear_family');
    await genotypeBrowser.familyFilters.familyTags.addTag('quad_family');
    await genotypeBrowser.familyFilters.familyTags.addTag('missing_dad_family');

    await genotypeBrowser.tablePreviewButtonId.click();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('77 variants selected', { timeout: 120000 });


    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButtonId.click();
    const download = await downloadPromise;
    const fixtureData = scanCSV(
      'fixtures/genotype-browser/variants-3.tsv',
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
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const familyTags = genotypeBrowser.familyFilters.familyTags;
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyTagsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyTagsTab();

    await familyTags.toggleOr();

    await familyTags.removeTag('nuclear_family');
    await familyTags.addTag('affected_dad_family');
    await familyTags.addTag('quad_family');
    await familyTags.addTag('affected_mom_family');
    await familyTags.removeTag('affected_prb_family');
    await familyTags.removeTag('affected_sib_family');
    await familyTags.addTag('unaffected_prb_family');
    await familyTags.addTag('missing_dad_family');

    await genotypeBrowser.saveQueryDropdownButton.click();
    await expect(genotypeBrowser.linkInput).not.toHaveValue('');
    const url = await genotypeBrowser.linkInput.inputValue();
    await page.goto(url);
    await genotypeBrowser.waitForLoaded();

    await expect(familyTags.tagRemove('nuclear_family')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(familyTags.tagAdd('affected_dad_family')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(familyTags.tagAdd('quad_family')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(familyTags.tagAdd('affected_mom_family')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(familyTags.tagRemove('affected_prb_family')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(familyTags.tagRemove('affected_sib_family')).toHaveCSS('color', 'rgb(255, 0, 0)');
    await expect(familyTags.tagAdd('unaffected_prb_family')).toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(familyTags.tagAdd('missing_dad_family')).toHaveCSS('color', 'rgb(0, 128, 0)');
  });

  test('should clear all tags that are selected in Family Tags', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const familyTags = genotypeBrowser.familyFilters.familyTags;
    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.familyTagsTab).toBeVisible();
    await genotypeBrowser.familyFilters.openFamilyTagsTab();

    await expect(familyTags.root).toBeVisible();

    await familyTags.addTag('nuclear_family');
    await familyTags.removeTag('quad_family');

    await genotypeBrowser.tablePreviewButtonId.click();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('15 variants selected', { timeout: 120000 });

    await familyTags.clearFilters();
    await expect(familyTags.tagAdd('nuclear_family')).not.toHaveCSS('color', 'rgb(0, 128, 0)');
    await expect(familyTags.tagRemove('quad_family')).not.toHaveCSS('color', 'rgb(255, 0, 0)');

    await genotypeBrowser.tablePreviewButtonId.click();
    await expect(genotypeBrowser.variantsCountSpan).toHaveText('92 variants selected', { timeout: 120000 });
  });

  test('should display pheno filters panel after "Advanced" button click', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.familyFilters.advancedTab).toBeVisible();
    await genotypeBrowser.familyFilters.openAdvancedTab();

    await expect(genotypeBrowser.familyFilters.multiContinuousFilter).toBeVisible();
    await expect(genotypeBrowser.familyFilters.selectContinuousFilterHint).toBeVisible();

    await genotypeBrowser.familyFilters.advancedSearchBox.click();
    await genotypeBrowser.familyFilters.advancedMeasureOption('instrument_1.age').click();
    await expect(genotypeBrowser.familyFilters.histogram).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.advancedTab).not.toBeVisible();
  });

  test('errors state reset when opening Pheno Measures tab and switch tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.familyFilters.phenoMeasuresRoleTab).toBeVisible();
    await genotypeBrowser.familyFilters.phenoMeasuresRoleTab.click();

    await expect(genotypeBrowser.familyFilters.phenoMeasures.personFiltersSelector).toBeVisible();
    await expect(genotypeBrowser.familyFilters.phenoMeasures.selectMeasureHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();

    await genotypeBrowser.openToolLink('Gene browser');

    await genotypeBrowser.openToolLink('Genotype browser');
    await expect(genotypeBrowser.familyFilters.phenoMeasuresRoleTab).toBeVisible();

    await expect(genotypeBrowser.familyFilters.phenoMeasures.personFiltersSelector).not.toBeVisible();
    await expect(genotypeBrowser.familyFilters.phenoMeasures.selectMeasureHint).not.toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
  });
});

test.describe('Pheno Measures tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, datasetIds.denovoHelloWorld, 'Genotype browser');
  });

  test('pheno measures panel', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await expect(genotypeBrowser.familyFilters.phenoFiltersPanel).not.toBeVisible();
    await genotypeBrowser.familyFilters.openPhenoMeasuresToggle();
    await expect(genotypeBrowser.familyFilters.phenoFiltersPanel).toBeVisible();
    await expect(genotypeBrowser.familyFilters.phenoMeasures.selectMeasureHint).toBeVisible();
    await expect(genotypeBrowser.familyFilters.phenoMeasures.measuresDropdownContainer).toBeVisible();
  });

  test('if Pheno Measures tab is enabled in Genotype browser for different studies', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    await utils.navigateToDatasetPage(page, datasetIds.allGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.phenoMeasuresTab).not.toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.iossifov2014Liftover, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.phenoMeasuresTab).not.toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.helloWorldGenotypes, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.phenoMeasuresTab).toBeVisible();

    await utils.navigateToDatasetPage(page, datasetIds.vcfHelloWorld, 'Genotype browser');
    await expect(genotypeBrowser.familyFilters.phenoMeasuresTab).toBeVisible();
  });

  test('measures order and dropdown content update when adding measures', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_3').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_1').click();

    await phenoMeasures.measuresSearchInput.click();
    await expect(phenoMeasures.measureOption('instrument_1.iq')).not.toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_3')).not.toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_1')).not.toBeVisible();

    await expect(phenoMeasures.personFilters).toHaveCount(3);
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_1');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.measure_3');
    await expect(phenoMeasures.personFilterTitle(2)).toContainText('instrument_1.iq');
  });

  test('measures order and dropdown content update when removing measures', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_4').click();

    await expect(phenoMeasures.personFilters).toHaveCount(3);

    await phenoMeasures.removeButton('instrument_2.measure_6').click();
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_4');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.age');

    await phenoMeasures.removeButton('instrument_1.age').click();
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_4');

    await phenoMeasures.removeButton('instrument_1.measure_4').click();

    await expect(phenoMeasures.personFilters).toHaveCount(0);
    await phenoMeasures.measuresSearchInput.click();
    await expect(phenoMeasures.measureOption('instrument_1.age')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_2.measure_6')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_4')).toBeVisible();
  });

  test('searching and selecting pheno measure', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.focus();
    await page.keyboard.type('iq');

    await expect(phenoMeasures.measureOption('instrument_1.iq')).toBeVisible();
    await phenoMeasures.measureOption('instrument_1.iq').click();
    await expect(genotypeBrowser.familyFilters.measuresTextbox).toBeEmpty();
    await expect(phenoMeasures.personFilters).toContainText('instrument_1.iq');
  });

  test('searching and selecting pheno measure with arrows and enter', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.focus();
    await page.keyboard.type('measure');

    await expect(phenoMeasures.measureOption('instrument_1.measure_1')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_2')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_3')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_4')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_1.measure_5')).toBeVisible();
    await expect(phenoMeasures.measureOption('instrument_2.measure_6')).toBeVisible();

    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');

    await expect(phenoMeasures.personFilters).toContainText('instrument_1.measure_3');
  });
  test('searching invalid pheno measure', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.focus();
    await page.keyboard.type('invalidMeasure');

    await expect(phenoMeasures.measureOption('Nothing found')).toBeVisible();
    await expect(phenoMeasures.selectMeasureHint).toBeVisible();
  });

  test('resetting pheno measures state when changing tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await expect(phenoMeasures.personFilters).toHaveCount(2);

    await genotypeBrowser.familyFilters.openAllTab();
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await expect(phenoMeasures.personFilters).toHaveCount(0);
    await expect(phenoMeasures.selectMeasureHint).toBeVisible();
  });

  test('resetting pheno measures state when changing tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await expect(phenoMeasures.personFilters).toHaveCount(2);
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    await genotypeBrowser.switchToTool('Phenotype browser');
    await genotypeBrowser.switchToTool('Genotype browser');
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();

    await expect(phenoMeasures.personFilters).toHaveCount(0);
    await expect(phenoMeasures.selectMeasureHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('resetting invalid pheno measures continuous histogram state when changing tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await expect(phenoMeasures.personFilters).toHaveCount(2);

    await phenoMeasures.personFilters.nth(0).locator('#from-input-field').clear();
    await phenoMeasures.personFilters.nth(0).locator('#from-input-field').pressSequentially('-100');

    await expect(phenoMeasures.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.familyFilters.openAllTab();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await expect(phenoMeasures.personFilters).toHaveCount(0);
    await expect(phenoMeasures.selectMeasureHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('resetting invalid pheno measures categorical histogram state when changing tab', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_5').click();

    await phenoMeasures.selectMode('dropdown selector');

    await expect(phenoMeasures.pleaseSelectValueHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await genotypeBrowser.familyFilters.openAllTab();
    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();

    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await expect(phenoMeasures.personFilters).toHaveCount(0);
    await expect(phenoMeasures.selectMeasureHint).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();
  });

  test('if error state is reset when removing histogram in invalid state', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await expect(phenoMeasures.personFilters).toHaveCount(2);

    await phenoMeasures.startInput('instrument_2.measure_6').clear();
    await phenoMeasures.startInput('instrument_2.measure_6').pressSequentially('-100');
    await expect(phenoMeasures.rangeStartBelowMinError).toBeVisible();
    await expect(genotypeBrowser.tablePreviewButton).toBeDisabled();
    await expect(genotypeBrowser.shareSaveButton).toBeDisabled();
    await expect(genotypeBrowser.downloadButton).toBeDisabled();

    await phenoMeasures.removeButton('instrument_2.measure_6').click();

    await expect(genotypeBrowser.tablePreviewButton).toBeEnabled();
    await expect(genotypeBrowser.shareSaveButton).toBeEnabled();
    await expect(genotypeBrowser.downloadButton).toBeEnabled();
  });

  test('downloaded file with multiple selected pheno measures', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_1').click();

    const measure1 = phenoMeasures.personFilterFor('instrument_1.measure_1');

    await measure1.locator('#from-input-field').clear();
    await measure1.locator('#from-input-field').pressSequentially('47.141');
    await measure1.locator('#to-input-field').clear();
    await measure1.locator('#to-input-field').pressSequentially('60.839');

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.age').click();

    const measure2 = phenoMeasures.personFilterFor('instrument_1.age');

    await measure2.locator('#to-input-field').clear();
    await measure2.locator('#to-input-field').pressSequentially('111.06');

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('fixtures/genotype-browser/variants-5.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('share/save query with multiple selected pheno measures', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_5').click();

    await expect(phenoMeasures.personFilters).toHaveCount(3);
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_5');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.iq');
    await expect(phenoMeasures.personFilterTitle(2)).toContainText('instrument_2.measure_6');

    await genotypeBrowser.saveQueryDropdownButton.click();
    await expect(genotypeBrowser.linkInput).not.toHaveValue('');
    const url = await genotypeBrowser.linkInput.inputValue();
    await page.goto(url);
    await genotypeBrowser.waitForLoaded();

    await expect(phenoMeasures.personFilters).toHaveCount(3);
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_5');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.iq');
    await expect(phenoMeasures.personFilterTitle(2)).toContainText('instrument_2.measure_6');
  });

  test('select role, select one bar and check downloaded file', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_5').click();

    await phenoMeasures.selectRole('instrument_1.measure_5', 'sib');

    await phenoMeasures.selectMode('click selector');
    await phenoMeasures.histogramBar('val4').click();

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();

    const download = await downloadPromise;
    const fixtureData = scanCSV('fixtures/genotype-browser/variants-4.tsv', {sep: '\t'});
    const downloadData = scanCSV(await download.path(), {sep: '\t'});
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('family id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('family id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });

  test('select measures and roles and check loaded query', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_4').click();


    await phenoMeasures.selectRole('instrument_1.measure_4', 'mom');
    await phenoMeasures.selectRole('instrument_1.measure_4', 'dad');

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_5').click();

    await phenoMeasures.selectRole('instrument_1.measure_5', 'sib');

    await expect(phenoMeasures.personFilters).toHaveCount(2);
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_5');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.measure_4');

    await genotypeBrowser.saveQueryDropdownButton.click();
    await expect(genotypeBrowser.linkInput).not.toHaveValue('');
    const url = await genotypeBrowser.linkInput.inputValue();
    await page.goto(url);
    await genotypeBrowser.waitForLoaded();

    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_5');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.measure_4');
    await expect(phenoMeasures.rolesList.nth(0).locator('.role-wrapper')).toContainText('sib');
    await expect(phenoMeasures.rolesList.nth(1).locator('.role-wrapper').nth(0)).toContainText('mom');
    await expect(phenoMeasures.rolesList.nth(1).locator('.role-wrapper').nth(1)).toContainText('dad');
  });

  test('selecting role and checking histogram', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await expect(phenoMeasures.sumOfBarsLabel).toHaveText('~191 (100.00%)');
    await expect(phenoMeasures.histogramFromLabel).toHaveText('From (Min: -11.1093)');
    await expect(phenoMeasures.histogramToLabel).toHaveText('To (Max: 174.2897)');

    await phenoMeasures.selectRole('instrument_1.iq', 'prb');

    await expect(phenoMeasures.sumOfBarsLabel).toHaveText('~39 (100.00%)');
    await expect(phenoMeasures.histogramFromLabel).toHaveText('From (Min: 12.9578)');
    await expect(phenoMeasures.histogramToLabel).toHaveText('To (Max: 150.2109)');
  });

  test('selecting, removing and updating dropdown enabled roles', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.selectRole('instrument_1.iq', 'prb');
    await checkIfRoleIsDisabled(phenoMeasures, 'prb');

    await phenoMeasures.selectRole('instrument_1.iq', 'mom');
    await checkIfRoleIsDisabled(phenoMeasures, 'mom');

    await expect(phenoMeasures.roleWrappers).toHaveCount(2);
    await expect(phenoMeasures.roleWrappers.nth(0)).toContainText('prb');
    await expect(phenoMeasures.roleWrappers.nth(1)).toContainText('mom');

    await phenoMeasures.removeRole('instrument_1.iq', 'prb');

    await expect(phenoMeasures.roleWrappers).toHaveCount(1);
    await expect(phenoMeasures.roleWrappers.nth(0)).toContainText('mom');

    await checkIfRoleIsEnabled(phenoMeasures, 'prb');

    await phenoMeasures.removeRole('instrument_1.iq', 'mom');
    await expect(phenoMeasures.roleWrappers).toHaveCount(0);
    await checkIfRoleIsEnabled(phenoMeasures, 'mom');
  });

  test('selecting role by typing and enter', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.roleSearchBox.pressSequentially('mo');
    await expect(phenoMeasures.roleOption('mom')).toBeVisible();
    await expect(phenoMeasures.roleOption('dad')).toBeHidden();
    await expect(phenoMeasures.roleOption('prb')).toBeHidden();
    await expect(phenoMeasures.roleOption('sib')).toBeHidden();


    await page.keyboard.press('Enter');
    await expect(phenoMeasures.roleSearchBox).toBeEmpty();
    await expect(phenoMeasures.roleWrappers).toHaveCount(1);
    await expect(phenoMeasures.roleWrappers.nth(0)).toContainText('mom');

    await phenoMeasures.roleSearchBox.click();
    await expect(phenoMeasures.roleOption('mom')).toBeDisabled();
    await expect(phenoMeasures.roleOption('dad')).toBeEnabled();
    await expect(phenoMeasures.roleOption('prb')).toBeEnabled();
    await expect(phenoMeasures.roleOption('sib')).toBeEnabled();
    await phenoMeasures.roleSearchBox.blur();
  });

  test('typing invalid role', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.roleSearchBox.focus();
    await page.keyboard.type('po');
    await expect(phenoMeasures.roleOptions).toHaveCount(0);

    await page.keyboard.press('Enter');
    await expect(phenoMeasures.roleWrappers).toHaveCount(0);
    await expect(phenoMeasures.roleSearchBox).toBeEmpty();

    await phenoMeasures.roleSearchBox.click();
    await expect(phenoMeasures.roleOption('mom')).toBeEnabled();
    await expect(phenoMeasures.roleOption('dad')).toBeEnabled();
    await expect(phenoMeasures.roleOption('prb')).toBeEnabled();
    await expect(phenoMeasures.roleOption('sib')).toBeEnabled();
    await phenoMeasures.roleSearchBox.blur();
  });

  test('histograms order when updating roles list of a measure', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.iq').click();

    await phenoMeasures.selectRole('instrument_1.iq', 'mom');

    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_3').click();

    await phenoMeasures.selectRole('instrument_1.measure_3', 'dad');

    await expect(phenoMeasures.personFilters).toHaveCount(2);
    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_3');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.iq');

    await phenoMeasures.selectRole('instrument_1.iq', 'sib');

    await phenoMeasures.removeRole('instrument_1.iq', 'mom');

    await expect(phenoMeasures.personFilterTitle(0)).toContainText('instrument_1.measure_3');
    await expect(phenoMeasures.personFilterTitle(1)).toContainText('instrument_1.iq');
    await expect(phenoMeasures.rolesList.nth(0).locator('.role-wrapper')).toContainText('dad');
    await expect(phenoMeasures.rolesList.nth(1).locator('.role-wrapper')).toContainText('sib');
  });

  test('filtering by pheno measures in family filters and person filters', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await phenoMeasures.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_1').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('6 variants selected');

    await genotypeBrowser.personFilters.openPhenoMeasuresTab();
    await genotypeBrowser.personFilters.measuresTextbox.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await genotypeBrowser.runTablePreview();
    await expect(genotypeBrowser.variantsCount).toHaveText('4 variants selected');
  });
  test('filtering by pheno measures in Phenotype Tool', async({ page }) => {
    const genotypeBrowser = new GenotypeBrowserPage(page);
    const phenoMeasures = genotypeBrowser.familyFilters.phenoMeasures;
    await utils.navigateToDatasetPage(page, utils.datasetIds.denovoHelloWorld, 'Phenotype tool');
    await page.locator('input#search-box').click();
    await page.getByText('instrument_1.age').click();

    await genotypeBrowser.familyFilters.openPhenoMeasuresTab();
    await genotypeBrowser.familyFilters.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_1.measure_4').click();

    await genotypeBrowser.familyFilters.measuresSearchInput.click();
    await phenoMeasures.measureOption('instrument_2.measure_6').click();

    await page.waitForResponse(
      resp => resp.url().includes('/api/v3/measures/role-list') && resp.status() === 200
    );

    const downloadPromise = page.waitForEvent('download', { timeout: 180000 });
    await genotypeBrowser.downloadButton.click();
    const download = await downloadPromise;

    const fixtureData = scanCSV('fixtures/pheno-tool/pheno_report18.csv');
    const downloadData = scanCSV(await download.path());
    const fixtureFrame = (await fixtureData.select(fixtureData.columns.sort()).collect()).sort('person_id');
    const downloadFrame = (await downloadData.select(downloadData.columns.sort()).collect()).sort('person_id');
    expect(fixtureFrame.toString()).toEqual(downloadFrame.toString());
  });
});

async function checkIfRoleIsDisabled(phenoMeasures: PersonFilters, role: string): Promise<void> {
  await phenoMeasures.roleSearchBox.click();
  await expect(phenoMeasures.roleOption(role)).toBeDisabled();
}

async function checkIfRoleIsEnabled(phenoMeasures: PersonFilters, role: string): Promise<void> {
  await phenoMeasures.roleSearchBox.click();
  await expect(phenoMeasures.roleOption(role)).toBeEnabled();
}
