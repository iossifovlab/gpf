import 'reflect-metadata';
import { plainToClass } from 'class-transformer';
import * as YAML from 'yaml';

import { EnrichmentToolData, Params } from "./dynamic-data-structure";
import { UsersPage } from "./users-page";
import { GenesBlockPage } from './genes-block-page';
import { EnrichmentModelsBockPage } from './enrichment-models-block-page';
import { GeneWeightsPage } from './gene-weights-page';

export const userData = {
  'unauthorized': {
    username: undefined,
    password: undefined,
    hasDatasetRights: false,
    sidenavElementsCount: 2,
    sidenavElements: ['Datasets', 'Autism gene profiles']
  },
  'normal': {
    username: 'research@iossifovlab.com',
    password: 'secret',
    hasDatasetRights: false,
    sidenavElementsCount: 3,
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles']
  },
  'admin': {
    username: 'admin@iossifovlab.com',
    password: 'secret',
    hasDatasetRights: true,
    sidenavElementsCount: 4,
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles', 'Management']
  },
};

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
  datasetStatistics: 'dataset-statistics',
  genotypeBrowser: 'genotype-browser',
  phenotypeBrowser: 'phenotype-browser',
  phenotypeTool: 'phenotype-tool',
  enrichmentTool: 'enrichment-tool',
  geneBrowser: 'gene-browser'
};

export const sidenavPageLinks = {
  datasets: 'datasets',
  savedQueries: 'saved-queries',
  autismGeneProfiles: 'autism-gene-profiles',
  management: 'management'
};

export class BasePage {
  private readonly adminUsername = 'admin@iossifovlab.com';
  private readonly adminPassword = 'secret';

  cleanup() {
    cy.clearCookie('sessionid')
  }

  preserveLogin() {
    Cypress.Cookies.preserveOnce('sessionid');
  }

  navigateToHome() {
    let baseUrl = Cypress.config().baseUrl;
    if(baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1);
    }
    cy.visit(`${baseUrl}/datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`);
  }

  login(username: string, password: string) {
    const usersPage = new UsersPage();

    if (!username || !password) {
      return;
    }

    usersPage.loginDropdownToggleButton.click();
    usersPage.usernameInput.type(username);
    usersPage.nextButton.click();
    usersPage.passwordInput.type(password);
    usersPage.loginSubmitButton.click();
    usersPage.logoutButton.should('be.visible');
  }

  loginAdmin() {
    this.login(this.adminUsername, this.adminPassword);
  }

  logout() {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
    cy.intercept('ALL_genotypes').as('allGenotypesRequest');
    cy.wait('@allGenotypesRequest');
  }

  navigateToDatasetPage(dataset: string, page: string) {
    this.openDatasetsDropdownMenu();
    this.datasetsDropdownMenuElements.contains(dataset).click();
    this.datasetsDropdownMenuButton.should('have.text', dataset);
    cy.get(`a.nav-link[href*="${page}"]`).click();
  }

  get datasetsDropdownMenuButton() {
    cy.get('#datasets-dropdown-menu-button').should('be.visible');
    return cy.get('#datasets-dropdown-menu-button');
  }

  get datasetsDropdownMenuElements() {
    cy.get('.dataset-selector a').should('be.visible');
    return cy.get('.dataset-selector a');
  }

  openDatasetsDropdownMenu() {
    this.datasetsDropdownMenuButton.click();
  }

  get sidenavTogglerButton() {
    return cy.get('.navbar-toggler-icon');
  }

  toggleSidenav() {
    this.sidenavTogglerButton.click({scrollBehavior: false});
  }

  navigateToSidenavPage(sidenavPageLink: string): void {
    this.sidenavTogglerButton.scrollIntoView();
    this.toggleSidenav();
    cy.get(`div.sidenav a[routerlink="/${sidenavPageLink}"]`).click({scrollBehavior: false});
  }

  findButtonInComponentContainingText(componentSelector: string, text: string) {
    return cy.get(componentSelector).contains(text);
  }
  
  findErrorAlertInComponent(componentSelector: string) {
    return cy.get(`${componentSelector} gpf-errors-alert .alert-danger`);
  }

  findWarningAlertInComponent(componentSelector: string) {
    return cy.get(`${componentSelector} .alert-warning`);
  }
}



// Pass path to yaml file using the '--env' flag in the cypress command:
// npx cypress open --config baseUrl=http://172.20.0.5/gpf/ --env yamlPath=cypress/iossifov.data.expected.yaml
export function parseYamlData(filePath: string): EnrichmentToolData[] {
  if (filePath === undefined) {
    return;
  }

  return plainToClass(EnrichmentToolData, YAML.parse(filePath) as EnrichmentToolData[]);
}

export function applyData(params: Params): void {
  const genesBlockPage = new GenesBlockPage();
  const geneWeightsPage = new GeneWeightsPage();
  const enrichmentModelsBockPage = new EnrichmentModelsBockPage();

  if (params.geneSymbols) {
    genesBlockPage.geneSymbolsButton.click();
    genesBlockPage.geneSymbolsTextarea.clear().type(params.geneSymbols.join(','));
  } else if (params.geneSet) {
    genesBlockPage.geneSetsButton.click();

    genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(params.geneSet.collection.id, {force: true});

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type(params.geneSet.id);
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(params.geneSet.id).click();

    if (params.geneSet.collection.id === 'Denovo' && params.geneSet.collection.affectedStatus) {
      // TODO
      // ...
      // ..
    }

  } else if (params.geneWeight) {
    genesBlockPage.geneWeightsButton.click();
    geneWeightsPage.dropdownButton.select(params.geneWeight.id);

    if (params.geneWeight.from) {
      geneWeightsPage.fromInputField.type(params.geneWeight.from.toString())
    }

    if (params.geneWeight.to) {
      geneWeightsPage.fromInputField.type(params.geneWeight.to.toString())
    }
  }

  if (params.models) {
    enrichmentModelsBockPage.selectModelsButton.click();

    if (params.models.backgroundModel) {
      enrichmentModelsBockPage.backgroundModelsDropdown.select(params.models.backgroundModel);
    }

    if (params.models.countingModel) {
      enrichmentModelsBockPage.countingModelsDropdown.select(params.models.countingModel);
    }
  }
}
