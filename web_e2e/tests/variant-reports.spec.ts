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
        expect(expectedFileLines).toHaveLength(downloadedFileLines.length);

        const columnToCheck = ['family_id', 'person_id', 'mom_id', 'dad_id', 'sex', 'status', 'role'];

        const expectedFileHeaders = expectedFileLines[0].split('\t');
        const expectedColIndexes = columnToCheck.map(col => expectedFileHeaders.indexOf(col));
        expect(expectedColIndexes).not.toContain(-1);

        const downloadedFileHeaders = expectedFileLines[0].split('\t');
        const downloadedColIndexes = columnToCheck.map(col => downloadedFileHeaders.indexOf(col));
        expect(downloadedColIndexes).not.toContain(-1);

        for (let i = 0; i < expectedFileLines.length; i++) {
          const expectedColData = expectedFileLines[i].split('\t');
          const downloadedColData = downloadedFileLines[i].split('\t');

          for (let k = 0; k < expectedColIndexes.length; k++) {
            expect(expectedColData[expectedColIndexes[k]]).toEqual(downloadedColData[downloadedColIndexes[k]]);
          }
        }
      });
    });
  });
});
