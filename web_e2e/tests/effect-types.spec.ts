import { test, expect } from '@playwright/test';
import * as utils from './utils';
import { EffectTypes } from './components/effect-types.component';

test.describe('Effect types tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    await effectTypes.clickButton('None');
    await expect(effectTypes.selectAtLeastOneError).toBeVisible();

    await effectTypes.clickButton('All');
    await expect(effectTypes.selectAtLeastOneError).not.toBeVisible();
  });

  test('should check/uncheck effect types checkboxes using "All" and "None" buttons', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    const listOfCheckboxes = await effectTypes.checkboxes.all();

    await effectTypes.clickButton('None');
    await Promise.all(listOfCheckboxes.map(async(el) => {
      await expect(el).not.toBeChecked();
    }));

    await effectTypes.clickButton('All');
    await Promise.all(listOfCheckboxes.map(async(el) => {
      await expect(el).toBeChecked();
    }));
  });

  test('should test checkboxes using "UTRs" button', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    const uncheckedEffectTypes = [
      'nonsense',
      'frame-shift',
      'splice-site',
      'no-frame-shift-newStop',
      'missense',
      'no-frame-shift',
      'noStart',
      'noEnd',
      'synonymous',
      'non-coding',
      'intron',
      'intergenic'
    ];

    await effectTypes.clickButton('UTRs');

    await expect(effectTypes.label('3\'UTR')).toBeChecked();
    await expect(effectTypes.label('5\'UTR')).toBeChecked();

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "LGDs" button', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    const checkedEffectTypes = [
      'nonsense',
      'frame-shift',
      'splice-site',
      'no-frame-shift-newStop',
    ];

    const uncheckedEffectTypes = [
      'missense',
      'no-frame-shift',
      'noStart',
      'noEnd',
      'synonymous',
      'non-coding',
      'intron',
      'intergenic',
      '3\'UTR',
      '5\'UTR'
    ];

    await effectTypes.clickButton('LGDs');
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "Nonsynonymous" button', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    const checkedEffectTypes = [
      'nonsense',
      'frame-shift',
      'splice-site',
      'no-frame-shift-newStop',
      'missense',
      'no-frame-shift',
      'noStart',
      'noEnd'
    ];

    const uncheckedEffectTypes = [
      'synonymous',
      'non-coding',
      'intron',
      'intergenic',
      '3\'UTR',
      '5\'UTR'
    ];

    await effectTypes.clickButton('Nonsynonymous');
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "Coding" button', async({ page }) => {
    const effectTypes = new EffectTypes(page);
    const checkedEffectTypes = [
      'nonsense',
      'frame-shift',
      'splice-site',
      'no-frame-shift-newStop',
      'missense',
      'no-frame-shift',
      'noStart',
      'noEnd',
      'synonymous'
    ];

    const uncheckedEffectTypes = [
      'non-coding',
      'intron',
      'intergenic',
      '3\'UTR',
      '5\'UTR'
    ];

    await effectTypes.clickButton('Coding');
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(effectTypes.label(type)).not.toBeChecked();
    }));
  });
});
