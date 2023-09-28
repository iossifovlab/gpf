import { test, expect, Page } from '@playwright/test';
import * as utils from './utils';

test.describe('Variant reports tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.login(page);
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.getByText(utils.datasetIds.iossifov2014, {exact: true}).click();
    await page.getByText('Dataset Statistics').click();
  });

  [
    {index: 0, name: 'first'},
    {index: 1, name: 'second'},
    {index: 5, name: 'fifth'}
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
        const downloadedFileLines: string[] = files[0].split(/\r\n|\r|\n/);
        const expectedFileLines: string[] = files[1].split(/\r\n|\r|\n/);

        const expectedColNames = expectedFileLines[0].split('\t');
        const columnIndexToCheck = ['family_id', 'person_id', 'mo_id', 'dad_id', 'sex', 'status', 'role']
          .map(col => expectedColNames.indexOf(col));

        for (let i = 0; i < expectedFileLines.length; i++) {
          const expectedColData = expectedFileLines[i].split('\t');
          const downloadedColData = downloadedFileLines[i].split('\t');

          columnIndexToCheck.forEach(index => {
            expect(expectedColData[index]).toEqual(downloadedColData[index]);
          });
        }
      });
    });
  });
});
