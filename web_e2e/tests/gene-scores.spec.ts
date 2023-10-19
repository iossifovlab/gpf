/* eslint-disable indent */
import { test, expect } from '@playwright/test';
import * as utils from './utils';

const geneScoresData = [
  {
    desc: 'SFARI gene score',
    inputField: false,
    allVariants: '30'
  },
  {
    desc: 'RVIS rank',
    inputField: true,
    allVariants: '0'
  },
  {
    desc: 'RVIS',
    inputField: true,
    allVariants: '0'
  },
  {
    desc: 'LGD rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'LGD score',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pLI rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pLI',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pRec rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pRec',
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

  test('should display gene scores panel', async({ page }) => {
    await expect(page.locator('#gene-scores-panel')).not.toBeVisible();
    await page.locator('#gene-scores').click();
    await expect(page.locator('#gene-scores-panel')).toBeVisible();
  });

  test('should show all the gene scores in the selector dropdown', async({ page }) => {
    await page.locator('#gene-scores').click();

    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    geneScoresData.forEach(async geneScore => {
      await expect(page.locator('gpf-gene-scores select')).toContainText(geneScore.desc);
    });
  });

  geneScoresData.forEach(geneScore => {
    test(
        'should go through all gene scores and check whether the from/to buttons are shown or hidden for '
            + `${geneScore.desc}`,
         async({ page }) => {
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select').selectOption(geneScore.desc);
    await expect(page.locator('input#from-input-field')).toBeVisible({visible: geneScore.inputField});
    await expect(page.locator('input#to-input-field')).toBeVisible({visible: geneScore.inputField});
  });

  test('should have working from/to step up/down buttons in RVIS rank', async({ page }) => {
    await page.locator('#gene-scores').click();
    await page.locator('gpf-gene-scores select').selectOption('RVIS rank');

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
            await page.locator('gpf-gene-scores select').selectOption('ExAC pLI');

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
    });
});