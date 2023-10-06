import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';
import { readCSV } from 'nodejs-polars';

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

      await Promise.all([
        utils.readFile(await download.path()),
        utils.readFile(`playwright/fixtures/variant-reports/families${cell.index}.ped`)
      ]).then((files: [string, string]) => {
        const fixtureData = readCSV(files[0], {sep: '\t', columns: cell.columnsToCheck});
        const downloadData = readCSV(files[1], {sep: '\t', columns: cell.columnsToCheck});
        expect(fixtureData.frameEqual(downloadData)).toBe(true);
      });
    });
  });
});
