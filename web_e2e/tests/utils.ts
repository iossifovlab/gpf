import { Page, expect } from '@playwright/test';

// For local replace with http://172.xx.x.x/gpf
export const instanceUrl = process.env.GPF_STAGING_INSTANCE_URL ?
  process.env.GPF_STAGING_INSTANCE_URL : 'http://gpf:8080/gpf';
// Replace with http://localhost:8025 if testing local
export const mailhogUrl = 'http://mailhog:8025';
export const username = process.env.GPF_STAGING_USERNAME ? process.env.GPF_STAGING_USERNAME : 'admin@iossifovlab.com';
export const password = process.env.GPF_STAGING_PASSWORD ? process.env.GPF_STAGING_PASSWORD : 'secret';

export const datasetIds = {
  allGenotypes: 'ALL Genotypes',
  compGenotypes: 'COMP Genotypes',
  compDenovo: 'comp_denovo',
  compVcf: 'comp_vcf',
  compAll: 'comp_all',
  iossifov2014: 'iossifov_2014',
  multi: 'multi'
};

export const toolPageLinks = {
  datasetDescription: 'dataset-description',
  datasetStatistics: 'dataset-statistics',
  genotypeBrowser: 'genotype-browser',
  phenotypeBrowser: 'phenotype-browser',
  phenotypeTool: 'phenotype-tool',
  enrichmentTool: 'enrichment-tool',
  geneBrowser: 'gene-browser'
};

export async function logout(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Log Out' }).click();
}

export async function login(page: Page, user = username, pass = password): Promise<void> {
  if (user === undefined || pass === undefined) {
    return;
  }
  await page.locator('#log-in-button').click();
  expect(page.url()).toContain('login');

  await page.locator('#id_username').fill(user);
  await page.locator('#id_password').fill(pass);
  await Promise.all([
    await page.waitForLoadState(),
    await page.locator('.login-button').click()
  ]);

  await page.waitForSelector('#log-out-button');
}

export async function loginAdmin(page: Page, user = username, pass = password): Promise<void> {
  await login(page, user, pass);
}

export async function navigateToHome(page: Page, dataset = 'ALL_genotypes'): Promise<void> {
  await page.goto(`${page.url()}datasets/${dataset}/${toolPageLinks.geneBrowser}`);
}

export async function navigateToDatasetPage(page: Page, dataset: string, tool: string): Promise<void> {
  await page.locator('#header a:text("Datasets")').click();
  await page.waitForSelector('gpf-datasets');
  await expect(page.getByText('Loading datasets...')).not.toBeVisible();
  await page.locator('#datasets-dropdown-menu-button').click();
  await page.locator('a').filter({ hasText: dataset }).click();
  await expect(page.locator('#datasets-dropdown-menu-button')).toHaveText(dataset);
  await page.locator('a').filter({ hasText: `${tool}`}).click();
}

export function readFile(name): Promise<unknown> {
  const fs = require('fs');
  return new Promise((resolve, reject) => {
    fs.readFile(name, function(err, data) {
      if (err) {
        reject(err);
      }
      resolve(data);
    });
  });
}

export function getRandomString(): string {
  return Math.random().toString(36).substring(2, 9);
}

// Create user without password
export async function createUser(page: Page, email: string, name: string): Promise<void> {
  await page.locator('#create-user-form-button').click();

  await page.waitForSelector('.grid-container'); // In case of duplicates
  if (await page.locator(`[id="${email}-user-cell"]`).isVisible() === true) {
    await page.locator(`[id="${email}-delete-user-button"]`).click();
    await page.locator('button:text("Delete")').click();
    await page.waitForSelector(`[id="${email}-user-cell"]`, {state: 'detached'});
  }

  await page.locator('#name-box').fill(name);
  await page.locator('#email-box').fill(email);
  await page.locator('#create-user-button').click();


  await expect(page.locator(`[id="${email}-user-cell"]`)).toBeVisible();
  await expect(page.locator(`[id="${email}-password-cell"]`)).toBeEmpty();
}

// export async function navigateToDatasetPage(dataset: string, page: string, hasAccessRights = true): void {
//   this.openDatasetsDropdownMenu();
//   this.datasetsDropdownMenuElements.contains(dataset).should('be.visible').click({force: true});
//   this.datasetsDropdownMenuButton.should('have.text', dataset);
//   cy.get(`a.nav-link[href*="${page}"]`).click();

//   this.waitForPageToLoad(page, hasAccessRights);
// }
