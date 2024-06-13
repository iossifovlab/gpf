/* eslint-disable indent */
import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';

test.describe('Genes block tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'comp_all', 'Genotype browser');
  });

  test('should display gene symbols panel', async({ page }) => {
    await expect(page.locator('#gene-symbols-panel')).toBeHidden();

    await page.click('#gene-symbols');
    await expect(page.locator('#gene-symbols-panel')).toBeVisible();
  });

  test('should display error alert in gene symbols panel when the textarea is empty', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Symbols' }).click();
    await expect(page.getByRole('alert')).toBeVisible();

    await page.fill('textarea', 'SAMD11');
    await expect(page.getByRole('alert')).toBeHidden();
  });

  test('should display gene sets panel', async({ page }) => {
    await expect(page.locator('.gene-sets-panel')).toBeHidden();
    await page.getByRole('tab', { name: 'Gene Sets' }).click();
    await expect(page.locator('#gene-sets-panel')).toBeVisible();
  });

  test('should display error alert in gene sets panel when the textarea is empty', async({ page }) => {
    await page.getByRole('tab', { name: 'Gene Sets' }).click();
    await expect(page.locator('css=.alert-danger')).toBeVisible();

    await page.click('input#search-box');
    await page.fill('input#search-box', 'non-essential genes');

    await page.getByText('non-essential genes').click();
    await expect(page.locator('css=.alert-danger')).not.toBeVisible();
  });

  test('should display gene weights panel', async({ page }) => {
    await expect(page.locator('#gene-scores-panel')).toBeHidden();

    await page.getByRole('tab', { name: 'Gene Scores' }).click();
    await expect(page.locator('#gene-scores-panel')).toBeVisible();
  });
});


test.describe('Genes block gene sets names and count tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'comp_all', 'Genotype browser');
  });
    [
        {
          collection: 'Main',
          expectedSearchCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. ' +
            'Low load for disruptive mutations in autism genes and their biased transmission. PNAS (2015)',
          expectedDownloadCount: '239'
        },
        {
          collection: 'SFARI Genes',
          expectedSearchCondition: 'SFARI ALL (910): SFARI Genes (2017-09): All genes',
          expectedDownloadCount: '910'
        },

      ].forEach(data => {
        test('should properly display "' + data.expectedSearchCondition + '" in "' +
        data.collection + '" collection, and the counts should match', async({ page }) => {
            await utils.navigateToDatasetPage(page, 'iossifov_2014', 'Genotype browser');
            await page.getByRole('tab', { name: 'Gene Sets' }).click();
            await page.locator('select#selected-collection').selectOption(data.collection);
            await page.waitForRequest(utils.instanceUrl + '/api/v3/gene_sets/gene_sets');
            await page.getByPlaceholder('Select or start typing to search').click();

            const expectedSetName = data.expectedSearchCondition;
            const geneSetName = expectedSetName.substring(0, expectedSetName.indexOf('(') - 1);

            await page.getByPlaceholder('Select or start typing to search').pressSequentially(geneSetName);
            await page.waitForResponse(
                resp => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
            );
            await page.waitForLoadState('load');

            await page.locator('.sets-dropdown mat-option').first().click();

            await expect(page.locator('span#selected-value')).toContainText(expectedSetName);

            const actualCountElement = await page.locator(
                'span:has-text("Count:")'
            ).textContent();
            const actualCount = actualCountElement.replace('Count: ', '').replace(' (Download)', '').trim();
            const expectedCount = data.expectedDownloadCount;
            expect(actualCount).toEqual(expectedCount);
          });
        });
    });


test.describe('Gene block download tests ', () => {
test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'ALL Genotypes', 'Gene browser');
});

[
    {
      collection: 'Main',
      expectedSearchCondition: 'autism candidates from Iossifov PNAS 2015 (239): Iossifov I., et al. ' +
        'Low load for disruptive mutations in autism genes and their biased transmission. PNAS (2015)'
    },
    {
      collection: 'Protein domains',
      expectedSearchCondition: 'ABH (18):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedSearchCondition: 'let-7 (881):'
    },
    {
      collection: 'miRNA from Darnell',
      expectedSearchCondition: 'miR-124 (1018):'
    }
].forEach(data => {
     test('should download "' + data.expectedSearchCondition + '" in the "' + data.collection +
     '" collection and check whether the count in the name should matches ' +
     'the downloaded"s file length and the gene set"s name matches the first value of the file', async({ page }) => {
    const results = [];

    await utils.navigateToDatasetPage(page, 'iossifov_2014', 'Genotype Browser');

    await page.locator('#gene-sets').click();
    await page.locator('gpf-gene-sets select.form-control').selectOption(data.collection);

    results.splice(0, results.length);
    let expectedName = data.expectedSearchCondition;
    const geneSetName = expectedName.substring(0, expectedName.indexOf('(') - 1);
    const expectedCount = Number(expectedName.substring(expectedName.indexOf('(') + 1, expectedName.indexOf(')')));

    await page.locator('gpf-gene-sets select.form-control').selectOption(data.collection);
    await page.getByPlaceholder('Select or start typing to search').click();
    await page.getByPlaceholder('Select or start typing to search').focus();
    await page.keyboard.type(geneSetName);
    await page.waitForResponse(
      resp => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
  );

    await page.waitForLoadState('load');
    await page.locator('.sets-dropdown mat-option').first().click();

    const downloadPromise = page.waitForEvent('download');
    await page.locator('a.download-link').click();
    const downloadedFile = (await downloadPromise).createReadStream();
    const expectedLines = [];
    for await (const line of await downloadedFile) {
        expectedLines.push(String(line));
    }

    expectedLines.map((text: string) => {
        const textLines = text.split(/\r\n|\r|\n/);
        expect(textLines.length - 2).toBe(expectedCount);
        expectedName = expectedName.replace(/\s*\(\d+\)\s*/, '');
        expect(textLines[0].replace(/^"(.*)"$/, '$1').trim()).toBe(expectedName);
      });
    });
  });
});

test.describe('Genes block denovo gene set gene symbols tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, { waitUntil: 'load' });
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, 'iossifov_2014', 'Genotype browser');
  });

  test(
    'should download iossifov affected ' +
      'denovo gene sets and check whether they are equal to the reference data', async({ page }) => {
        await utils.navigateToDatasetPage(page, 'iossifov_2014', 'Genotype browser');
        await page.locator('#gene-sets').click();
        await expect(page.locator('#gene-sets-panel')).toBeVisible();
        await page.locator('gpf-gene-sets select.form-control').selectOption({ label: 'Denovo' });

        await page.getByPlaceholder('Select or start typing to search').click();
        await page.getByPlaceholder('Select or start typing to search').focus();
        await page.keyboard.type('Missense');
        await page.waitForResponse(
          (resp) => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
        );

        await page.locator('.sets-dropdown mat-option')
          .getByText('Missense')
          .first()
          .click();

        const download = page.waitForEvent('download');
        const downloadData = [];
        await page.locator('a.download-link').click();

        for await (const chunk of await (await download).createReadStream()) {
          downloadData.push(chunk);
        }

        // Assert that the downloaded file contents are the same as the expected file contents

        const expectedDataLines = (
          await utils.readFile(path.join(__dirname +
            '/../fixtures/gene-sets/Missense_iossifov_2014_status_affected.csv'))
        ).toString();

        const downloadedData = Buffer.concat(downloadData);
        const downloadedDataLines = downloadedData.toString();

        expect(downloadedDataLines.split('\n').sort()).toEqual(expectedDataLines.split('\n').sort());
    }
  );

    test(
      'should download iossifov unaffected denovo gene sets and '
      + 'check whether they are equal to the reference data', async({ page }) => {
          await utils.navigateToDatasetPage(page, 'iossifov_2014', 'Genotype browser');
          await page.locator('#gene-sets').click();
          await expect(page.locator('#gene-sets-panel')).toBeVisible();
          await page.locator('gpf-gene-sets select.form-control').selectOption({ label: 'Denovo' });

          await page.isChecked('#iossifov_2014-checkbox-affected'); // wait for gpfjs state first
          await page.locator('#iossifov_2014-checkbox-affected').click();
          await page.locator('#iossifov_2014-checkbox-unaffected').click();

          await page.getByPlaceholder('Select or start typing to search').click();
          await page.getByPlaceholder('Select or start typing to search').focus();
          await page.keyboard.type('LGDs');
          await page.waitForResponse(
            (resp) => resp.url().includes('/api/v3/gene_sets/gene_sets') && resp.status() === 200
          );

          await page.locator('.sets-dropdown mat-option')
            .getByText('LGDs')
            .first()
            .click();

          const download = page.waitForEvent('download');
          const downloadData = [];
          await page.locator('a.download-link').click();

          for await (const chunk of await (await download).createReadStream()) {
            downloadData.push(chunk);
          }

          // Assert that the downloaded file contents are the same as the expected file contents

          const expectedDataLines = (
            await utils.readFile(path.join(__dirname + '/../fixtures/gene-sets/LGDs_iossifov_2014_unaffected.csv'))
          ).toString();

          const downloadedData = Buffer.concat(downloadData);
          const downloadedDataLines = downloadedData.toString();

          expect(downloadedDataLines.split('\n').sort()).toEqual(expectedDataLines.split('\n').sort());
        }
    );
});

