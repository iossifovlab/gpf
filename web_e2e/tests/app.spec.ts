import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('App tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
  });

  test('should open oauth login window on login button click', async({ page }) => {
    await page.goto(`${page.url()}/datasets/ALL_genotypes/${utils.toolPageLinks.geneBrowser}`);
    await page.locator('#log-in-button').click();

    await expect(page.locator('input#id_username')).toBeVisible();
    await expect(page.locator('input#id_password')).toBeVisible();
  });

  test('should display "GPF: Genotypes and Phenotypes in Families" as a title', async({ page }) => {
    await utils.loginWorkerUser(page);
    const titleElement = page.title();

    const titleText = await titleElement;
    expect(titleText).toBe('GPF: Genotypes and Phenotypes in Families');
  });

  test('should click on the "Datasets" button and ' +
     'navigate to "/datasets/ALL_genotypes/gene-browser"', async({ page }) => {
    const expectedUrl = `${utils.frontendUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.geneBrowser}`;

    await utils.loginWorkerUser(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Gene browser');

    const currentUrl = page.url();

    expect(currentUrl).toBe(expectedUrl);
  });

  test('should click on the "User profile" button and navigate to "/user-profile"', async({
    page
  }) => {
    const savedQueriesUrl = `${utils.frontendUrl}/user-profile`;

    await utils.loginWorkerUser(page);
    await page.locator('a:text("User Profile")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(savedQueriesUrl);
  });

  // tb-nxl: the "Management button → /management" test moved to
  // user-management.spec.ts — it asserts on the admin group's Management
  // tab and so requires loginLiteralAdmin.

  test('should click on the "Gene profiles" button and ' +
     'navigate to "/autism-gene-profiles"', async({ page }) => {
    const geneProfilesUrl = `${utils.frontendUrl}/gene-profiles`;

    await utils.loginWorkerUser(page);
    await page.locator('#header a:text("Gene Profiles")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(geneProfilesUrl);
  });
});

test.describe('App user access rights tests', () => {
  // tb-nxl: admin entry was deliberately removed; the admin nav-bar
  // assertion lives in user-management.spec.ts (it requires
  // loginLiteralAdmin to see the Management tab).
  const userData = {
    unauthorized: {
      username: undefined,
      password: undefined,
      hasDatasetRights: false,
      navigationTabsCount: 2,
      navigationTabs: ['Datasets', 'Gene profiles']
    },
    normal: {
      username: 'research@iossifovlab.com',
      password: 'secret',
      hasDatasetRights: false,
      navigationTabsCount: 5,
      navigationTabs: ['Home', 'Datasets', 'Gene profiles', 'User profile', 'About']
    },
  };

  test.beforeEach(async({ page }) => {
    await page.goto(utils.frontendUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
  });

  Object.values(userData).filter(
    login => login.username !== undefined && login.password !== undefined
  ).forEach(data => {
    test(`should check navigation bar for the right elements for ${data.username} user`, async({ page }) => {
      await utils.login(page, data.username as string, data.password as string);

      await expect(page.locator('#header a')).toHaveCount(data.navigationTabsCount);

      for (const tab of data.navigationTabs) {
        await expect(page.locator('#header a').getByText(tab)).toBeVisible();
      }
    });
  });

  test('should properly disable tools based on access rights', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Dataset Description');
    await expect(page.locator('li').filter({hasText: 'Gene Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Enrichment Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Description'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Statistics'})).toHaveClass('nav-item disabled-tool');


    await utils.loginWorkerUser(page);
    await expect(page.locator('li').filter({hasText: 'Gene Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Genotype Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Enrichment Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Description'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Statistics'})).toHaveClass('nav-item disabled-tool');

    await utils.logout(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.helloWorldGenotypes, 'Dataset Description');
    await expect(page.locator('li').filter({hasText: 'Gene Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Genotype Browser'})).toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Browser'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Enrichment Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Phenotype Tool'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Description'})).not.toHaveClass('nav-item disabled-tool');
    await expect(page.locator('li').filter({hasText: 'Dataset Statistics'})).toHaveClass('nav-item disabled-tool');
  });

  test('should check that an authenticated worker user sees the phenotype and ' +
    'transmitted icons in the dimmed-but-visible style', async({ page }) => {
    await utils.loginWorkerUser(page);
    await page.locator('a:text("Datasets")').click();
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.waitForSelector('div.dropdown-menu');
    await utils.expandDataset(page, utils.datasetIds.compDenovoLiftover);
    await utils.expandDataset(page, utils.datasetIds.denovoHelloWorld);

    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.vcfHelloWorld }).locator('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
    await expect(
      page.locator('gpf-dataset-node a')
        .filter({ hasText: utils.datasetIds.vcfHelloWorld }).locator('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(126, 126, 126)');
  });

  test('should login researcher and check whether the phenotype and transmitted icons ' +
    'have the correct color', async({ page }) => {
    await utils.login(page, userData.normal.username, userData.normal.password);
    await page.locator('a:text("Datasets")').click();
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.waitForSelector('div.dropdown-menu');
    await utils.expandDataset(page, utils.datasetIds.compDenovoLiftover);
    await utils.expandDataset(page, utils.datasetIds.denovoHelloWorld);
    await expect(page.locator('#register-alert')).toBeVisible();

    await expect(
      page.locator('gpf-dataset-node a').filter({ hasText: utils.datasetIds.vcfHelloWorld }).locator('.phenotype-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');
    await expect(
      page.locator('gpf-dataset-node a')
        .filter({ hasText: utils.datasetIds.vcfHelloWorld }).locator('.transmitted-icon')
    ).toHaveCSS('color', 'rgb(220, 220, 220)');
  });

  // tb-nxl: the two "give user access rights" tests (Hello World and ALL
  // Genotypes) moved to user-management.spec.ts — they create users via
  // /management, which requires the admin group via loginLiteralAdmin.

  test('if Gene Browser tool is opened by default', async({ page }) => {
    await page.locator('a').filter({ hasText: 'Datasets'}).click();
    await expect(page.locator('gpf-gene-browser')).toBeVisible();

    await utils.loginWorkerUser(page);
    await expect(page.locator('gpf-gene-browser')).toBeVisible();

    await utils.logout(page);
    await expect(page.locator('gpf-home')).toBeVisible();
    await page.locator('a').filter({ hasText: 'Datasets'}).click();
    await expect(page.locator('gpf-gene-browser')).toBeVisible();
  });

  // tests robustness of the authentication process
  test('should login and logout repeatedly', async({ page }) => {
    for (let i = 0; i < 3; i++) {
      /* eslint-disable no-await-in-loop */
      await utils.loginWorkerUser(page);
      await utils.logout(page);
      /* eslint-enable */
    }
  });
});
