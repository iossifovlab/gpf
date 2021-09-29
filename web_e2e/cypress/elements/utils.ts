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
    const baseUrl = Cypress.config().baseUrl;
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
    usersPage.loginDropdownToggleButton.should('be.visible');
  }

  navigateToDatasetPage(dataset: string, page: string) {
    this.openDatasetsDropdownMenu();
    this.datasetsDropdownMenuElements.contains(dataset).click();
    this.datasetsDropdownMenuButton.should('have.text', dataset);
    cy.get(`a.nav-link[href*="${page}"]`).click();
  }

  get datasetsDropdownMenuButton() {
    return cy.get('#datasets-dropdown-menu-button');
  }

  get datasetsDropdownMenuElements() {
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
