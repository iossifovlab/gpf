import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('Effect types tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAllLiftover, 'Genotype browser');
  });

  test('should display error alert when none of the checkboxes are selected', async({ page }) => {
    await page.locator('gpf-effect-types').getByText('None').click();
    await expect(page.getByText('Select at least one.')).toBeVisible();

    await page.locator('gpf-effect-types').getByText('All').click();
    await expect(page.getByText('Select at least one.')).not.toBeVisible();
  });

  test('should check/uncheck effect types checkboxes using "All" and "None" buttons', async({ page }) => {
    const listOfCheckboxes = await page.locator('gpf-effect-types input').all();

    await page.locator('gpf-effect-types').getByText('None').click();
    await Promise.all(listOfCheckboxes.map(async(el) => {
      await expect(el).not.toBeChecked();
    }));

    await page.locator('gpf-effect-types').getByText('All').click();
    await Promise.all(listOfCheckboxes.map(async(el) => {
      await expect(el).toBeChecked();
    }));
  });

  test('should test checkboxes using "UTRs" button', async({ page }) => {
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

    await page.locator('gpf-effect-types').getByText('UTRs').click();

    await expect(page.getByLabel('3\'UTR', { exact: true })).toBeChecked();
    await expect(page.getByLabel('5\'UTR', { exact: true })).toBeChecked();

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "LGDs" button', async({ page }) => {
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

    await page.locator('gpf-effect-types').getByText('LGDs').click();
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "Nonsynonymous" button', async({ page }) => {
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

    await page.locator('gpf-effect-types').getByText('Nonsynonymous').click();
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));
  });

  test('should test checkboxes using "Coding" button', async({ page }) => {
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

    await page.locator('gpf-effect-types').getByRole('button', { name: 'Coding' }).click();
    await Promise.all(checkedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).toBeChecked();
    }));

    await Promise.all(uncheckedEffectTypes.map(async(type) => {
      await expect(page.getByLabel(type, { exact: true })).not.toBeChecked();
    }));
  });
});