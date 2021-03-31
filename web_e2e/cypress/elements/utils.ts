import { UsersPage } from "./users-page";

export const userData = {
  'unauthorized': {
    username: undefined,
    password: undefined,
    sidenavElementsCount: 2,
    sidenavElements: ['Datasets', 'Autism gene profiles']
  },
  'normal': {
    username: 'research@iossifovlab.com',
    password: 'secret',
    sidenavElementsCount: 3,
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles']
  },
  'admin': {
    username: 'admin@iossifovlab.com',
    password: 'secret',
    sidenavElementsCount: 4,
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles', 'Management']
  },
};

export const datasetIds = {
  compAll: 'comp_all',
  compDenovo: 'comp_denovo',
  compVcf: 'comp_vcf',
  iossifov2014: 'iossifov_2014',
  multi: 'multi'
};

export const toolPageNames = {
  datasetStatistics: 'Dataset Statistics',
  genotypeBrowser: 'Genotype Browser',
  phenotypeBrowser: 'Phenotype Browser',
  phenotypeTool: 'Phenotype Tool',
  enrichmentTool: 'Enrichment Tool',
  geneBrowser: 'Gene Browser'
};

export class BasePage {
  private readonly adminUsername = 'admin@iossifovlab.com';
  private readonly adminPassword = 'secret';


  navigateToHome() {
    const baseUrl = Cypress.config().baseUrl;
    cy.visit(`${baseUrl}/datasets/comp_all/commonReport`);
  }

  login(username: string, password: string) {
    const usersPage = new UsersPage();

    if (!username || !password) {
      return;
    }

    usersPage.loginDropdownToggleButton.click();
    usersPage.usernameInput.type(username);
    usersPage.passwordInput.type(password);
    usersPage.loginSubmitButton.click();
  }

  loginAdmin() {
    this.login(this.adminUsername, this.adminPassword);
    cy.wait(500);
  }

  logout() {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
  }

  navigateToDatasetPage(dataset: string, page: string) {
    cy.get('#datasets-dropdown-menu-button').click();
    cy.get('a.dropdown-item').contains(dataset).click();
    cy.get('a.nav-link').contains(page).click();
  }

  toggleSidenav() {
    cy.get('.navbar-toggler-icon').click();
    // cy.wait(1000); // Waits for the animation to finish
  }

  get sidenavDatasetButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/datasets"]');
  }

  get sidenavSavedQueriesButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/queries"]');
  }

  get sidenavAutismGeneProfilesButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/autismGeneProfiles"]');
  }

  get sidenavManagementButton() {
    return cy.get('div > .sidenav-container > .sidenav  > .nav > .nav-item > a[routerlink="/management"]');
  }

  findButtonInComponentContainingText(componentSelector: string, text: string) {
    return cy.get(componentSelector).contains(text);
  }
}
