import { UsersPage } from "./users-page";

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
    const baseUrl = Cypress.config().baseUrl;
    cy.visit(`${baseUrl}/datasets/comp_all/${toolPageLinks.datasetStatistics}`);
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
    cy.get('#logout-button').should('be.visible');
  }

  loginAdmin() {
    this.login(this.adminUsername, this.adminPassword);
  }

  logout() {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
  }

  navigateToDatasetPage(dataset: string, page: string) {
    cy.get('#datasets-dropdown-menu-button').click();
    cy.get('a.dropdown-item[style="opacity: 1;"]').should('have.length', Object.keys(datasetIds).length);
    cy.get('a.dropdown-item[style="opacity: 1;"]').contains(dataset).click();
    cy.get('#datasets-dropdown-menu-button').should('have.text', dataset + ' ');
    cy.get(`a.nav-link[routerlink="${page}"]`).click();
  }

  toggleSidenav() {
    cy.get('.navbar-toggler-icon').click();
  }

  get sidenavDatasetButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/datasets"]');
  }

  get sidenavSavedQueriesButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/saved-queries"]');
  }

  get sidenavAutismGeneProfilesButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/autism-gene-profiles"]');
  }

  get sidenavManagementButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/management"]');
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
