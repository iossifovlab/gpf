import { test, expect } from '@playwright/test';
import * as utils from './utils';

test.describe('App tests', () => {
  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
  });

  test('should open oauth login window on login button click', async({ page }) => {
    await page.goto(`${page.url()}/datasets/ALL_genotypes/${utils.toolPageLinks.geneBrowser}`);
    await page.locator('#log-in-button').click();

    await expect(page.locator('input#id_username')).toBeVisible();
    await expect(page.locator('input#id_password')).toBeVisible();
  });

  test('should display "GPF: Genotypes and Phenotypes in Families" as a title', async({ page }) => {
    await utils.loginAdmin(page);
    const titleElement = page.title();

    const titleText = await titleElement;
    expect(titleText).toBe('GPF: Genotypes and Phenotypes in Families');
  });

  test('should click on the "Datasets" button and ' +
     'navigate to "/datasets/ALL_genotypes/gene-browser"', async({ page }) => {
    const expectedUrl = `${utils.instanceUrl}/datasets/ALL_genotypes/${utils.toolPageLinks.geneBrowser}`;

    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Gene browser');

    const currentUrl = page.url();

    expect(currentUrl).toBe(expectedUrl);
  });

  test('should click on the "User profile" button and navigate to "/user-profile"', async({
    page
  }) => {
    const savedQueriesUrl = `${utils.instanceUrl}/user-profile`;

    await utils.loginAdmin(page);
    await page.locator('a:text("User Profile")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(savedQueriesUrl);
  });

  test('should click on the "User Management" button and navigate to "/management"', async({ page }) => {
    const managementUrl = `${utils.instanceUrl}/management`;

    await utils.loginAdmin(page);

    await page.locator('a:text("User Management")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(managementUrl);
  });

  test('should click on the "Gene profiles" button and ' +
     'navigate to "/autism-gene-profiles"', async({ page }) => {
    const geneProfilesUrl = `${utils.instanceUrl}/gene-profiles`;

    await utils.loginAdmin(page);
    await page.locator('a:text("Gene Profiles")').click();

    const currentUrl = page.url();

    expect(currentUrl).toBe(geneProfilesUrl);
  });
});

test.describe('App user access rights tests', () => {
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
    admin: {
      username: 'admin@iossifovlab.com',
      password: 'secret',
      hasDatasetRights: true,
      navigationTabsCount: 6,
      navigationTabs: ['Home', 'Datasets', 'Gene profiles', 'User profile', 'User Management', 'About']
    }
  };

  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
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

  test('should go through all tools and check whether the permission denied prompt ' +
       'is displayed when not logged in and not displayed when logged in with admin account', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await page.getByText('Gene Browser').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await page.getByText('Phenotype Tool').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await page.getByText('Phenotype Browser').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await page.getByText('Genotype Browser').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await page.getByText('Dataset Statistics').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await utils.loginAdmin(page);
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await page.getByText('Gene Browser').click();
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await page.getByText('Phenotype Tool').click();
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await page.getByText('Phenotype Browser').click();
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await page.getByText('Genotype Browser').click();
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await page.getByText('Dataset Statistics').click();
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();
  });


  test('should login admin and check whether the datasets have the correct opacity value', async({ page }) => {
    await utils.login(page, userData.admin.username, userData.admin.password);
    await page.locator('a:text("Datasets")').click();
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.waitForSelector('div.dropdown-menu');

    for (let i = 0; i < Object.keys(utils.datasetIds).length; i++) {
      await expect(page.locator('.dataset-dropdown-item').nth(i)).toHaveCSS('opacity', '1');
    }
  });

  test('should login researcher and check whether the datasets have the correct opacity value', async({ page }) => {
    await utils.login(page, userData.normal.username, userData.normal.password);
    await page.locator('a:text("Datasets")').click();
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();
    await page.locator('#datasets-dropdown-menu-button').click();
    await page.waitForSelector('div.dropdown-menu');

    for (let i = 0; i < Object.keys(utils.datasetIds).length; i++) {
      await expect(page.locator('a.dataset-dropdown-item').nth(i)).toHaveCSS('opacity', '0.3');
    }
  });

  test('should login admin and give researcher access rights for comp_vcf, ' +
       'then login researcher and verify his rights', async({ page }) => {
    await utils.loginAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await page.locator('a:text("User Management")').click();
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).fill('COMP_genotypes');
    await page.locator('button.add-item-button').filter({ hasText: 'COMP_genotypes' }).click();
    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText(email).first().click();
    await page.locator('#preview-plain > a').click();

    await page.goto(
      utils.instanceUrl + '/'
      + (await page.locator('#preview-plain > a').getAttribute('href')).split('gpf')[2], {waitUntil: 'load'}
    );

    await page.locator('#id_new_password1').fill(userData.normal.password + '!!__3456');
    await page.locator('#id_new_password2').fill(userData.normal.password + '!!__3456');
    await page.locator('.login-button').click();

    await utils.logout(page);
    await utils.login(page, email, userData.normal.password + '!!__3456');
    await utils.navigateToDatasetPage(page, utils.datasetIds.compVcf, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();
    await expect(page.locator('gpf-variant-reports')).toBeVisible();

    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype Browser');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compDenovo, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compGenotypes, 'Genotype Browser');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.multi, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();
  });

  test('should login admin and give researcher access rights for ALL Genotypes, ' +
     'then login researcher and verify his rights', async({ page }) => {
    await utils.loginAdmin(page);
    const username = utils.getRandomString();
    const email = `${username}@mail.com`;

    await page.locator('a:text("User Management")').click();
    await utils.createUser(page, email, username);

    await page.locator(`[id="${email}-groups-cell"]`).getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).fill('ALL_genotypes');
    await page.getByRole('button', { name: 'ALL_genotypes', exact: true }).click();
    await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();

    await page.locator(`[id="${email}-reset-password-button"] > button`).click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText(email).first().click();
    await page.locator('#preview-plain > a').click();

    await page.goto(
      utils.instanceUrl + '/'
      + (await page.locator('#preview-plain > a').getAttribute('href')).split('gpf')[2], {waitUntil: 'load'}
    );

    await page.locator('#id_new_password1').fill(userData.normal.password + '!!__3456');
    await page.locator('#id_new_password2').fill(userData.normal.password + '!!__3456');
    await page.locator('.login-button').click();

    await expect(page).toHaveURL(`${utils.instanceUrl}/datasets/ALL_genotypes/gene-browser`);
    await expect(page.locator('#log-out-button')).toBeVisible();
    await utils.logout(page);

    await utils.login(page, email, userData.normal.password + '!!__3456');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype Browser');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compDenovo, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.iossifov2014, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compGenotypes, 'Genotype Browser');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.compAll, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();

    await utils.navigateToDatasetPage(page, utils.datasetIds.multi, 'Dataset Statistics');
    await expect(page.locator('#permission-denied-prompt')).not.toBeVisible();
  });
});

