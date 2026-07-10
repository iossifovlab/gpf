import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { PhenoToolMeasure } from './components/pheno-tool-measure.component';

test.describe('Pheno tool measure tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Phenotype tool');
  });

  test('should check if the dropdown menu closes when clicking outside', async({ page }) => {
    const measure = new PhenoToolMeasure(page);
    await measure.searchBox.click();
    await expect(measure.measuresDropdown).toBeVisible();

    await page.mouse.click(0, 0);
    await expect(measure.measuresDropdown).not.toBeVisible();
  });

  test('should check whether when the measure is empty, an error message appears' +
  'and the normalization checkboxes get disabled', async({ page }) => {
    const measure = new PhenoToolMeasure(page);
    await expect(measure.pleaseSelectMeasureError).toBeVisible();
    await expect(measure.normalizationCheckbox('Age')).toBeDisabled();
    await expect(measure.normalizationCheckbox('Non verbal IQ')).toBeDisabled();

    await measure.selectMeasure('instrument_1.measure_1');
    await expect(measure.pleaseSelectMeasureError).not.toBeVisible();
    await expect(measure.normalizationCheckbox('Age')).not.toBeDisabled();
    await expect(measure.normalizationCheckbox('Non verbal IQ')).not.toBeDisabled();

    await measure.clearMeasureButton.click();
    await expect(measure.pleaseSelectMeasureError).toBeVisible();
    await expect(measure.normalizationCheckbox('Age')).toBeDisabled();
    await expect(measure.normalizationCheckbox('Non verbal IQ')).toBeDisabled();
  });

  test('should check if the normalization checkboxes get disabled when' +
  'the measure is the same as the normalization criteria', async({ page }) => {
    const measure = new PhenoToolMeasure(page);
    await measure.selectMeasure('instrument_1.age');
    await expect(measure.normalizationCheckbox('Age')).toBeDisabled();

    await measure.clearMeasureButton.click();
    await measure.selectMeasure('instrument_1.iq');
    await expect(measure.normalizationCheckbox('Non verbal IQ')).toBeDisabled();
  });

  test('should check the remove button with selected measure', async({ page }) => {
    const measure = new PhenoToolMeasure(page);
    await measure.selectMeasure('instrument_1.age');

    await measure.clearMeasureButton.click();
    await expect(measure.searchBox).toBeEmpty();
  });

  [
    {
      searchText: 'age',
      options: ['instrument_1.age']
    },
    {
      searchText: 'm',
      options: ['instrument_1.measure_1', 'instrument_1.measure_2', 'instrument_1.measure_3', 'instrument_1.measure_4']
    },
    {
      searchText: 'q',
      options: ['instrument_1.iq']
    },
  ].forEach(data => {
    test(`should type ${data.searchText} and check available measures`, async({ page }) => {
      const measure = new PhenoToolMeasure(page);
      await measure.searchBox.click();
      await measure.searchBox.fill(data.searchText);
      await Promise.all(data.options.map(async(option) => {
        await expect(measure.measureOption(option)).toBeVisible();
      }));
    });
  });
});
