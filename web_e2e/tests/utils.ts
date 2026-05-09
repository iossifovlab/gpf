import { Page, expect } from '@playwright/test';


// Jenkins/CI: hit the gpf-web-ui-prod Apache (frontend service)
// at root. The Apache config in web_ui/httpd.conf reverse-proxies
// /api/ and /ws/ to backend:9001, so frontendUrl == backendUrl
// (the SPA and the API are the same origin from the SPA's POV).
// Mail goes through the mailhog service `mail` on its UI port 8025.
// Local-dev URLs are kept commented below for reference.
export const frontendUrl = 'http://frontend';
export const backendUrl = frontendUrl;
export const mailhogUrl = 'http://mail:8025';

// for local dev with containers:
// export const frontendUrl = 'http://localhost:8080/gpf';
// export const backendUrl = frontendUrl;
// export const mailhogUrl = 'http://localhost:8025';

// for data-hg19-startup dev:
// export const backendUrl = 'http://localhost:8000';
// export const frontendUrl = 'http://localhost:4200';
// export const mailhogUrl = 'http://localhost:8025';

// tb-nxl: the `username` / `password` exports that lived here used to
// silently default `login(page)` to admin@iossifovlab.com — exactly the
// racy default this refactor exists to remove. The literal-admin
// fallback (including the GPF_STAGING_USERNAME / GPF_STAGING_PASSWORD
// env-var override for staging) now lives in tests/_literal_admin.ts,
// scoped to the one spec allowed to use literal admin
// (user-management.spec.ts).

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

// tb-nxl: signature tightened — `user` no longer defaults to admin. Bare
// `utils.login(page)` is now a TypeScript compile error (it used to
// silently log in as admin@iossifovlab.com via the dropped `username`
// export). Specs that want an isolated logged-in user use
// loginWorkerUser(page) below; the one spec that needs literal admin
// uses loginLiteralAdmin from tests/_literal_admin.ts. Bare explicit
// callsites like `utils.login(page, 'research@iossifovlab.com')`
// continue to work (the `pass` default of 'secret' covers the
// provisioned test users).
export async function login(page: Page, user: string, pass: string = 'secret'): Promise<void> {
  await page.locator('#log-in-button').click();
  expect(page.url()).toContain('login');

  await page.locator('#id_username').fill(user);
  await page.locator('#id_password').fill(pass);
  await Promise.all([
    page.waitForLoadState(),
    page.locator('.login-button').click(),
  ]);

  await page.waitForSelector('#log-out-button');
}

// tb-nxl: per-worker user pool. Reads Playwright's auto-exported
// TEST_PARALLEL_INDEX (bounded [0, workers-1], reused across retries) and
// logs in as e2e_worker_<N>@iossifovlab.com. Each worker writes to its own
// user row — no cross-spec admin-row sharing under workers=16.
//
// E2E_WORKER_COUNT (set by web_infra/compose-jenkins.yaml + Jenkinsfile.e2e,
// matched by import_data.sh's provisioning loop) bounds the pool. Out-of-range
// throws so a future workers bump that forgets the provisioning surfaces
// loudly instead of as a flaky 401.
export async function loginWorkerUser(page: Page): Promise<void> {
  const idx = parseInt(process.env.TEST_PARALLEL_INDEX ?? '0', 10);
  const poolSize = parseInt(process.env.E2E_WORKER_COUNT ?? '16', 10);
  if (idx >= poolSize) {
    throw new Error(
      `loginWorkerUser: TEST_PARALLEL_INDEX=${idx} exceeds pool size ` +
      `E2E_WORKER_COUNT=${poolSize}. Bump E2E_WORKER_COUNT in ` +
      `web_infra/compose-jenkins.yaml + Jenkinsfile.e2e (and the ` +
      `provisioning loop in web_e2e/gpf_e2e_instance/import_data.sh ` +
      `picks it up automatically) so each parallel worker has its own user.`,
    );
  }
  await login(page, `e2e_worker_${idx}@iossifovlab.com`, 'secret');
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

  await expect(async() => {
    await page.locator('#datasets-dropdown-menu-button').click();
    await expect(page.locator('gpf-dataset-node').nth(0)).toBeVisible();
  }).toPass({intervals: [1000]});
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

  await page.waitForSelector('.grid-cell'); // In case of duplicates
  if (await page.locator(`[id="${email}-user-cell"]`).isVisible() === true) {
    await page.locator(`[id="${email}-delete-user-button"]`).click();
    await page.locator('button:text("Delete")').click();
    await page.waitForSelector(`[id="${email}-user-cell"]`, {state: 'detached'});
  }

  await page.locator('.create-container').locator('#name-box').fill(name);
  await page.locator('.create-container').locator('#email-box').fill(email);
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

export async function searchInGeneProfilesTable(page: Page, searchValue: string): Promise<void> {
  const searchResponsePromise = page.waitForResponse(
    resp => resp.url().includes(
      `/api/v3/gene_profiles/table/rows?page=4&symbol=${searchValue}`
    ) && resp.status() === 200
  );

  // search
  await page.locator('input#gene-search-input').focus();
  await page.keyboard.type(searchValue);

  await searchResponsePromise;
  await expect(page.locator('.search-loading-icon')).toHaveCount(0);
}

