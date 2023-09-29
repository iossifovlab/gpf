import { Page, expect } from '@playwright/test';

export const instanceUrl = process.env.GPF_STAGING_INSTANCE_URL ? process.env.GPF_STAGING_INSTANCE_URL : 'http://172.21.0.6/gpf';
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

export const sidenavPageLinks = {
  datasets: 'datasets',
  userProfile: 'user-profile',
  autismGeneProfiles: 'autism-gene-profiles',
  management: 'management'
};

export async function login(page: Page, user = username, pass = password): Promise<void> {
  await page.locator('#log-in-button').click();
  expect(page.url()).toContain('login');

  await page.locator('#id_username').fill(user);
  await page.locator('#id_password').fill(pass);
  await Promise.all([
    await page.waitForLoadState(),
    await page.locator('.login-button').click()
  ]);

  await page.waitForSelector('#log-out-button');
  await expect(page.getByText('Loading datasets...')).not.toBeVisible();
  await page.waitForLoadState('networkidle');
}

export function readFile(name): Promise<unknown> {
  const fs = require('fs');
  return new Promise((resolve, reject) => {
    fs.readFile(name, function(err, data) {
      if (err) {
        reject(err);
      }
      resolve(data.toString());
    });
  });
}

// export async function navigateToDatasetPage(dataset: string, page: string, hasAccessRights = true): void {
//   this.openDatasetsDropdownMenu();
//   this.datasetsDropdownMenuElements.contains(dataset).should('be.visible').click({force: true});
//   this.datasetsDropdownMenuButton.should('have.text', dataset);
//   cy.get(`a.nav-link[href*="${page}"]`).click();

//   this.waitForPageToLoad(page, hasAccessRights);
// }
