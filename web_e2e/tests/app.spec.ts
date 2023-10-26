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

  test('should toggle sidenav, click on the "Datasets" button and ' +
     'navigate to "/datasets/ALL_genotypes/gene-browser"', async({ page }) => {
    const baseUrl = page.url();
    const expectedUrl = `${baseUrl}/ALL_genotypes/${utils.toolPageLinks.geneBrowser}`;

    await utils.loginAdmin(page);
    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Gene browser');

    const currentUrl = page.url();

    expect(currentUrl).toBe(expectedUrl);
  });

  test('should toggle sidenav, click on the "User profile" button and navigate to "/user-profile"', async({
    page
  }) => {
    const savedQueriesUrl = `${utils.instanceUrl}/user-profile`;

    await utils.loginAdmin(page);
    await utils.navigateToSidenavPage(page, utils.sidenavPageLinks.userProfile);

    const currentUrl = page.url();

    expect(currentUrl).toBe(savedQueriesUrl);
  });

  test('should toggle sidenav, click on the "Management" button and navigate to "/management"', async({ page }) => {
    const managementUrl = `${utils.instanceUrl}/management`;

    await utils.loginAdmin(page);

    await utils.navigateToSidenavPage(page, utils.sidenavPageLinks.management);

    const currentUrl = page.url();

    expect(currentUrl).toBe(managementUrl);
  });

  test('should toggle sidenav, click on the "Autism gene profiles" button and ' +
     'navigate to "/autism-gene-profiles"', async({ page }) => {
    const autismGeneProfilesUrl = `${utils.instanceUrl}/autism-gene-profiles`;

    await utils.loginAdmin(page);
    await utils.navigateToSidenavPage(page, utils.sidenavPageLinks.autismGeneProfiles);

    const currentUrl = page.url();

    expect(currentUrl).toBe(autismGeneProfilesUrl);
  });
});

test.describe('App user access rights tests', () => {
  const userData = {
    unauthorized: {
      username: undefined,
      password: undefined,
      hasDatasetRights: false,
      sidenavElementsCount: 2,
      sidenavElements: ['Datasets', 'Autism gene profiles']
    },
    normal: {
      username: 'research@iossifovlab.com',
      password: 'secret',
      hasDatasetRights: false,
      sidenavElementsCount: 3,
      sidenavElements: ['Datasets', 'Autism gene profiles', 'User profile']
    },
    admin: {
      username: 'admin@iossifovlab.com',
      password: 'secret',
      hasDatasetRights: true,
      sidenavElementsCount: 4,
      sidenavElements: ['Datasets', 'Autism gene profiles', 'User profile', 'Management']
    }
  };

  test.beforeEach(async({ page }) => {
    await page.goto(utils.instanceUrl, {waitUntil: 'load'});
    await utils.navigateToHome(page);
  });

  Object.values(userData).forEach(data => {
    test('should toggle sidenav bar with the right elements inside', async({ page }) => {
      if (data.username !== undefined && data.password !== undefined) {
        await utils.login(page, utils.username, utils.password);
        await expect(page.locator('div.sidenav a.nav-link')).not.toBeVisible();

        await page.locator('#sidenav-toggle-button').click();
        await expect(page.locator('div.sidenav a.nav-link')).toHaveCount(data.sidenavElementsCount);

        await page.locator('#sidenav-toggle-button').click();
        await expect(page.locator('div.sidenav a.nav-link')).not.toBeVisible();
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

  Object.values(userData).forEach(data => {
    test('should login with accounts with different access rights and check whether the datasets ' +
         'in the dropdown have the correct opacity value', async({ page }) => {
      if (data.username !== undefined || data.password !== undefined) {
        const expectedOpacity = data.hasDatasetRights ? '1' : '0.3';

        await utils.login(page, data.username as string, data.password as string);
        await page.locator('#datasets-dropdown-menu-button').click();

        const elements = page.locator('.dataset-selector a');
        for (const element of await elements.all()) {
          // eslint-disable-next-line no-await-in-loop
          const opacity = await page.evaluate((
            el
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          ) => window.getComputedStyle(el.elementHandles()[0]).opacity, element);
          expect(opacity).toBe(expectedOpacity);
        }
      }
    });
  });

  test('should validate that researcher has no rights', async({ page }) => {
    await utils.navigateToDatasetPage(page, utils.datasetIds.compVcf, 'Dataset Statistics');
    await utils.login(page, userData.normal.username, userData.normal.password);
    await expect(page.locator('#permission-denied-prompt')).toBeVisible();
  });


  test('should login admin and give researcher access rights for comp_vcf, ' +
       'then login researcher and verify his rights', async({ page }) => {
    await utils.loginAdmin(page);
    await utils.createUser(page, 'user_comp_vcf@iossifovlab.com', userData.normal.password);
    await page.locator('[id="user_comp_vcf\\@iossifovlab\\.com-groups-cell"]').getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).fill('COMP_genotypes');
    await page.locator('button.add-item-button').filter({ hasText: 'COMP_genotypes' }).click();
    await expect(page.locator('[id="user_comp_vcf@iossifovlab.com-password-cell"]')).toBeEmpty();

    await page.locator('[id="user_comp_vcf@iossifovlab.com-reset-password-button"] > button').click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText('user_comp_vcf@iossifovlab.com').first().click();
    await page.locator('#preview-plain > a').click();

    await page.goto(
      utils.instanceUrl + '/'
      + (await page.locator('#preview-plain > a').getAttribute('href')).split('gpf')[2], {waitUntil: 'load'}
    );

    await page.locator('#id_new_password1').fill(userData.normal.password + '!!__3456');
    await page.locator('#id_new_password2').fill(userData.normal.password + '!!__3456');
    await page.locator('.login-button').click();

    await utils.logout(page);
    await utils.login(page, 'user_comp_vcf@iossifovlab.com', userData.normal.password + '!!__3456');
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
    await utils.createUser(page, 'user_all_genotypes@iossifovlab.com', userData.normal.password);
    await page.locator('[id="user_all_genotypes\\@iossifovlab\\.com-groups-cell"]').getByRole(
      'button', { name: 'Add' }
    ).click();
    await page.getByRole('textbox', { name: 'Search' }).fill('ALL_genotypes');
    await page.locator('button.add-item-button').filter({ hasText: 'ALL_genotypes' }).click();
    await expect(page.locator('[id="user_all_genotypes@iossifovlab.com-password-cell"]')).toBeEmpty();

    await page.locator('[id="user_all_genotypes@iossifovlab.com-reset-password-button"] > button').click();
    await page.locator('button:text("Reset")').click();

    await page.goto(utils.mailhogUrl, {waitUntil: 'load'});
    await page.getByText('user_all_genotypes@iossifovlab.com').first().click();
    await page.locator('#preview-plain > a').click();

    await page.goto(
      utils.instanceUrl + '/'
      + (await page.locator('#preview-plain > a').getAttribute('href')).split('gpf')[2], {waitUntil: 'load'}
    );

    await page.locator('#id_new_password1').fill(userData.normal.password + '!!__3456');
    await page.locator('#id_new_password2').fill(userData.normal.password + '!!__3456');
    await page.locator('.login-button').click();

    await utils.navigateToDatasetPage(page, utils.datasetIds.allGenotypes, 'Genotype browser');
    await utils.logout(page);
    await utils.login(page, 'user_all_genotypes@iossifovlab.com', userData.normal.password + '!!__3456');
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

