/* eslint-disable indent */
import { test, expect } from '@playwright/test';
import * as utils from './utils';
import * as path from 'path';

const geneScoresData = [
  {
    desc: 'SFARI gene score - Evidence strength supporting a gene\'s association with autism',
    inputField: false,
    allVariants: '30'
  },
  {
    desc: 'RVIS rank - Gene rank after sorting by RVIS intolerance score',
    inputField: true,
    allVariants: '0'
  },
  {
    desc: 'pLI - Probability of Loss-of-Function Intolerance',
    inputField: true,
    allVariants: '30'
  }
];

test.describe('Gene scores tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
  });

  test('should display gene scores panel and dropdown', async({ page }) => {
    await expect(page.locator('#gene-scores-panel')).not.toBeVisible();
    await page.locator('#gene-scores').click();
    await expect(page.locator('#gene-scores-panel')).toBeVisible();

    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    geneScoresData.forEach(async geneScore => {
      await expect(page.locator('gpf-gene-scores select')).toContainText(geneScore.desc);
    });
  });

  geneScoresData.forEach(geneScore => {
    test(
        'should go through all gene scores and check whether the from/to buttons are shown or hidden for '
            + `${geneScore.desc}`, async({ page }) => {
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select').selectOption(geneScore.desc);
    await expect(page.locator('input#from-input-field')).toBeVisible({visible: geneScore.inputField});
    await expect(page.locator('input#to-input-field')).toBeVisible({visible: geneScore.inputField});
    });
  });

  test('should have working from/to step up/down buttons in RVIS rank', async({ page }) => {
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select')
    .selectOption('RVIS rank - The rank of the gene after sorting based of RVIS score.');

    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');

    await page.locator('.histogram-from .step.up').click();
    await page.waitForRequest(utils.instanceUrl + '/api/v3/gene_scores/partitions');
    await page.locator('.histogram-to .step.down').click();
    await page.waitForRequest(utils.instanceUrl + '/api/v3/gene_scores/partitions');
    await expect(page.locator('input#from-input-field')).toHaveValue('111.927');
    await expect(page.locator('input#to-input-field')).toHaveValue('16529.073');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('1');
    await expect(page.locator('input#to-input-field')).toHaveValue('16640');
  });

  test('should have working from/to step up/down buttons in ExAC pLI', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select').selectOption('pLI - ExAC pLI');

    await expect(page.locator('input#from-input-field')).toHaveValue('0');
    await expect(page.locator('input#to-input-field')).toHaveValue('1');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-to .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.00001');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.912');

    await page.locator('.histogram-from .step.up').click();
    await page.locator('.histogram-to .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.000011');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.832');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0.00001');
    await expect(page.locator('input#to-input-field')).toHaveValue('0.912');

    await page.locator('.histogram-to .step.up').click();
    await page.locator('.histogram-from .step.down').click();
    await expect(page.locator('input#from-input-field')).toHaveValue('0');
    await expect(page.locator('input#to-input-field')).toHaveValue('1');
  });

    geneScoresData.forEach(geneScore => {
      test(`should filter variants when "${geneScore.desc}" gene score is selected`, async({ page }) => {
        await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Genotype browser');
        await page.click('#gene-scores');
        await page.locator('gpf-gene-scores select').selectOption(geneScore.desc);

        await expect(page.locator('text#sumOfBarsLabel')).not.toContainText('~');

        await page.locator('gpf-effect-types').getByRole('button', { name: 'All' }).click();
        await page.getByRole('button', { name: 'Table Preview' }).click();

        await expect(page.locator('#variants-count-span')).toHaveText(`${geneScore.allVariants} variants selected`);
      });
    });

  test('should download RVIS score and compare the file to the reference data', async({ page }) => {
    await page.click('#gene-scores');

    await page.locator('gpf-gene-scores select')
    .selectOption('RVIS score - The score reflects the intolerance of a gene to genetic variants (RVIS)');
    const downloadPromise = page.waitForEvent('download');
    await page.click('gpf-gene-scores .download-link');
    const downloadedFile = await downloadPromise;

    const streamData = downloadedFile.createReadStream();
    const data = [];

    for await (const chunk of await streamData) {
      data.push(chunk);
    }

    const expectedVariantsPath = path.join(__dirname + '/../fixtures/gene-scores/scores.csv');
    const expectedFileLines = await utils.readFile(expectedVariantsPath);
    const downloadedData = Buffer.concat(data);
    expect(downloadedData.toString()).toEqual(expectedFileLines.toString());
  });
});