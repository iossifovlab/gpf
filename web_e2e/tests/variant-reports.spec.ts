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
      const fixtureFrame = await fixtureData.select().collect();
      const downloadFrame = await downloadData.select().collect();
      expect(fixtureFrame.frameEqual(downloadFrame)).toBe(true);
    });
  });
});
