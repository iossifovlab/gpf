import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';
import { readCSV, scanCSV } from 'nodejs-polars';

test.describe('Variant reports tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.getByText(utils.datasetIds.iossifov2014, {exact: true}).click();
    await page.getByText('Dataset Statistics').click();
  });

  test('should display the correct elements in the families by number tab', async({ page }) => {
    await page.getByText('Families by number').click();
    await expect(page.locator('#download-total-families')).toBeVisible();
    await expect(page.locator('#families-by-number-select')).toBeVisible();
    await expect(page.locator('#families-by-number-div')).toBeVisible();

    await page.getByText('De Novo variants').click();
    await expect(page.locator('#download-total-families')).not.toBeVisible();
    await expect(page.locator('#families-by-number-select')).not.toBeVisible();
    await expect(page.locator('#families-by-number-div')).not.toBeVisible();
  });

  test('should display the correct elements in the families by pedigree tab', async({ page }) => {
    await page.getByText('Families by pedigree').click();
    await expect(page.locator('#families-by-pedigree-select')).toBeVisible();
    await expect(page.locator('#download-button')).toBeVisible();
    await expect(page.locator('#families-by-pedigree-div')).toBeVisible();
    await expect(page.locator('#selected-tags-list')).toBeVisible();

    await page.getByText('De Novo variants').click();
    await expect(page.locator('#families-by-pedigree-select')).not.toBeVisible();
    await expect(page.locator('#download-button')).not.toBeVisible();
    await expect(page.locator('#families-by-pedigree-div')).not.toBeVisible();
    await expect(page.locator('#selected-tags-list')).not.toBeVisible();
  });

  test('should display the correct elements in the families by pedigree tab', async({ page }) => {
    await page.getByText('De Novo variants').click();
    await expect(page.locator('#denovo-variants-select')).toBeVisible();
    await expect(page.locator('#de-novo-variants-legend-report')).toBeVisible();
    await expect(page.locator('#denovo-variants-div')).toBeVisible();

    await page.getByText('Families by number').click();
    await expect(page.locator('#denovo-variants-select')).not.toBeVisible();
    await expect(page.locator('#de-novo-variants-legend-report')).not.toBeVisible();
    await expect(page.locator('#denovo-variants-div')).not.toBeVisible();
  });

  [
    {option: 'Affected Status', legendElements: ['affected', 'unaffected']},
    {option: 'Role', legendElements: ['mom', 'dad', 'proband', 'sibling']},
    {option: 'Phenotype', legendElements: ['autism', 'unaffected']}
  ].forEach(data => {
    test.skip('should check content of the legend for ' + data.option + ' option in the families by pedigree tab', async({ page }) => {
      await page.getByText('Families by pedigree').click();
      await expect(page.locator('#expand-legend-button')).toBeVisible();
      await expect(page.locator('#legend')).not.toBeVisible();
      await page.locator('#families-by-pedigree-select').selectOption(data.option);

      await page.locator('#expand-legend-button').click();
      await expect(page.locator('#legend')).toBeVisible();

      await expect(page.locator('.legend-item')).toHaveCount(data.legendElements.length);

      data.legendElements.forEach(el => {
        await expect(page.locator('#legend')).toContainText(el);
      });
    });
  });

  [
    {index: 0, name: 'first', columnsToCheck: ['family_id', 'person_id', 'mom_id', 'dad_id', 'sex', 'status', 'role']},
    {index: 1, name: 'second', columnsToCheck: ['family_id', 'person_id', 'mom_id', 'dad_id', 'sex', 'status', 'role']},
    {index: 5, name: 'fifth', columnsToCheck: ['family_id', 'person_id', 'mom_id', 'dad_id', 'sex', 'status', 'role']}
  ].forEach(cell => {
    test(`should download family counters report from ${cell.name} pedigree modal`, async({ page }) => {
      await page.locator('a:text("Families by pedigree")').click();
      await expect(page.locator('#families-by-pedigree')).toBeVisible();
      await page.locator('.pedigree-cell').nth(cell.index).click();

      let downloadPromise = page.waitForEvent('download');
      downloadPromise = page.waitForEvent('download');

      await page.locator('.modal-content >> #download-button').click();
      const download = await downloadPromise;

      const fixtureData = scanCSV(await download.path(), {sep: '\t'});
      const downloadData = scanCSV(`playwright/fixtures/variant-reports/families${cell.index}.ped`, {sep: '\t'});
      const fixtureFrame = await fixtureData.select(cell.columnsToCheck).collect();
      const downloadFrame = await downloadData.select(cell.columnsToCheck).collect();
      expect(fixtureFrame.frameEqual(downloadFrame)).toBe(true);
    });
  });
});
