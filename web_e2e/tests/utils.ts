import { Page, expect } from '@playwright/test';


export const frontendUrl = 'http://gpf:8080/gpf';
export const backendUrl = frontendUrl;
export const mailhogUrl = 'http://mailhog:8025';

// for local dev with containers:
// export const frontendUrl = 'http://localhost:8080/gpf';
// export const backendUrl = frontendUrl;
// export const mailhogUrl = 'http://localhost:8025';

// for data-hg19-startup dev:
// export const backendUrl = 'http://localhost:8000';
// export const frontendUrl = 'http://localhost:4200';
// export const mailhogUrl = 'http://localhost:8025';

export const username = process.env.GPF_STAGING_USERNAME ? process.env.GPF_STAGING_USERNAME : 'admin@iossifovlab.com';
export const password = process.env.GPF_STAGING_PASSWORD ? process.env.GPF_STAGING_PASSWORD : 'secret';

export const datasetIds = {
  allGenotypes: 'ALL Genotypes',
  compGenotypes: 'COMP Genotypes',
  compDenovoLiftover: 'comp_denovo_liftover',
  compVcfLiftover: 'comp_vcf_liftover',
  compAllLiftover: 'comp_all_liftover',
  iossifov2014Liftover: 'iossifov_2014_liftover',
  multiLiftover: 'multi_liftover',
  helloWorldGenotypes: 'Hello World Genotypes',
  denovoHelloWorld: 'denovo_helloworld',
  vcfHelloWorld: 'vcf_helloworld',
  phenoHelloWorld: 'pheno_helloworld',
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
  await page.waitForSelector('#log-in-button');
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
  await navigateToDataset(page, dataset);
  await page.locator('a').filter({ hasText: `${tool}`}).click();
}

export async function navigateToDataset(page: Page, dataset: string): Promise<void> {
  await openDatasetDropdown(page);
  await expandDataset(page, dataset);

  await expect(page.locator('gpf-dataset-node a').filter({ hasText: dataset })).toBeVisible();
  await page.locator('gpf-dataset-node a').filter({ hasText: dataset }).click();
  await expect(page.locator('#selected-dataset-name')).toHaveText(dataset);
}

export async function openDatasetDropdown(page: Page): Promise<void> {
  if (!await page.locator('gpf-datasets').isVisible()) {
    await page.locator('#header a:text("Datasets")').click({ force: true });
    await page.waitForSelector('gpf-datasets');
    await expect(page.getByText('Loading datasets...')).not.toBeVisible();
  }
  await page.locator('#datasets-dropdown-menu-button').click();
}

export async function expandDataset(page: Page, dataset: string): Promise<void> {
  /* eslint-disable no-await-in-loop */
  if (!await page.locator('gpf-dataset-node a').filter({ hasText: dataset }).isVisible()) {
    // close all datasets
    for (const ele of (await page.locator('.collapse-dataset-icon.rotate').all()).reverse()) {
      await ele.click();
    }

    // expand all datasets
    for (const ele of await page.locator('.collapse-dataset-icon').all()) {
      await expect(async() => {
        await ele.click();
        await expect(ele).toContainClass('rotate', {timeout: 5000});
      }).toPass({intervals: [1000]});
    }
  }
  /* eslint-enable */
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

export async function resetGeneProfiles(page: Page): Promise<void> {
  await page.waitForSelector('#reset-button');
  await page.locator('#reset-button').click();
  await page.waitForResponse(
    resp => resp.url().includes('/api/v3/users/user_gp_state') && resp.status() === 204
  );

  await expect(page.locator('#gene-search-input')).toBeEmpty();
  await expect(page.locator('#compare-genes-modal')).not.toBeVisible();
  await expect(page.locator('#tabs-wrapper')).toHaveText('All genes');
  await expect(page.locator('.header-cell')).toHaveCount(25);
  await expect(page.locator('.active-sort-header')).toContainText('Autism Gene Sets');
}

