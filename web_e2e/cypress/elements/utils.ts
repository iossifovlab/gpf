import { UsersPage } from "./users-page";

export const userData = {
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
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles']
  },
  admin: {
    username: 'admin@iossifovlab.com',
    password: 'secret',
    hasDatasetRights: true,
    sidenavElementsCount: 4,
    sidenavElements: ['Datasets', 'Saved queries', 'Autism gene profiles', 'Management']
  }
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

  public cleanup(): void {
    cy.clearCookie('sessionid')
  }

  public preserveLogin(): void {
    Cypress.Cookies.preserveOnce('sessionid');
  }

  public navigateToHome(): void {
    let baseUrl = Cypress.config().baseUrl;
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1);
    }
    cy.visit(`${baseUrl}/datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`);
  }

  public login(username: string, password: string): void {
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

  public loginAdmin(): void {
    this.login(this.adminUsername, this.adminPassword);
  }

  public logout(): void {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
    cy.intercept('ALL_genotypes').as('allGenotypesRequest');
    cy.wait('@allGenotypesRequest');
  }

  public navigateToDatasetPage(dataset: string, page: string): void {
    this.openDatasetsDropdownMenu();
    // this.datasetsDropdownMenuElements.contains(dataset).should('be.visible');
    this.datasetsDropdownMenuElements.contains(dataset).click();
    this.datasetsDropdownMenuButton.should('have.text', dataset);
    cy.get(`a.nav-link[href*="${page}"]`).click(); // add some sort of should here perhaps
  }

  public get datasetsDropdownMenuButton(): element {
    cy.get('#datasets-dropdown-menu-button').should('be.visible');
    return cy.get('#datasets-dropdown-menu-button');
  }

  public get datasetsDropdownMenuElements(): element {
    cy.get('.dataset-selector a').should('be.visible');
    return cy.get('.dataset-selector a');
  }

  public openDatasetsDropdownMenu(): void {
    this.datasetsDropdownMenuButton.click();
  }

  private get sidenavTogglerButton(): element {
    return cy.get('.navbar-toggler-icon');
  }

  public toggleSidenav(): void {
    this.sidenavTogglerButton.click({scrollBehavior: false});
  }

  public navigateToSidenavPage(sidenavPageLink: string): void {
    this.sidenavTogglerButton.scrollIntoView();
    this.toggleSidenav();
    cy.get(`div.sidenav a[routerlink="/${sidenavPageLink}"]`).click({scrollBehavior: false});
  }

  public findButtonInComponentContainingText(componentSelector: string, text: string): element {
    return cy.get(componentSelector).contains(text);
  }

  public findErrorAlertInComponent(componentSelector: string): element {
    return cy.get(`${componentSelector} gpf-errors-alert .alert-danger`);
  }

  public findWarningAlertInComponent(componentSelector: string): element {
    return cy.get(`${componentSelector} .alert-warning`);
  }
}
