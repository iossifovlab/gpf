import { UsersPage } from './users-page';

export const longTimeout = 35000;

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
  geneBrowser: 'gene-browser',
  home: 'home'
};

export const sidenavPageLinks = {
  datasets: 'datasets',
  userProfile: 'user-profile',
  geneProfiles: 'gene-profiles',
  management: 'management'
};

export class BasePage {
  private readonly adminUsername = 'admin@iossifovlab.com';
  private readonly adminPassword = 'secret';
  private oauthTokens = {
    refreshToken: {
      key: 'refresh_token',
      value: ''
    }
  };

  public preserveLogin(): void {
    Cypress.Cookies.preserveOnce('sessionid');
    Cypress.Cookies.preserveOnce('access_token');

    if (localStorage.length === 0) {
      localStorage.setItem(this.oauthTokens.refreshToken.key, this.oauthTokens.refreshToken.value);
    } else {
      this.oauthTokens.refreshToken.value = localStorage.getItem(this.oauthTokens.refreshToken.key);
    }
  }

  public cleanup(): void {
    cy.clearCookie('sessionid');
    cy.clearCookie('access_token');
    cy.getCookie('sessionid').should('be.null');
    cy.getCookie('access_token').should('be.null');
    localStorage.clear();
  }

  public navigateToHome(hasAccessRights = true): void {
    cy.visit(`${Cypress.config().baseUrl}datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`);
    this.waitForPageToLoad(toolPageLinks.geneBrowser, hasAccessRights);
  }

  private waitForLoginButtonWithRetries(retries = 10): Cypress.Chainable<void> {
    return cy.get('#log-in-button').if('not.visible').then(() => {
      if (retries === 0) {
        throw new Error('Cannot find Login button after multiple checks.');
      }
      return this.waitForLoginButtonWithRetries(--retries);
    });
  }

  public login(username: string, password: string, hasAccessRights = true, inAGP = false): void {
    this.waitForLoginButtonWithRetries();

    if (!inAGP) {
      cy.intercept('GET', '/gpf/api/v3/datasets').as('datasets');
    }

    const usersPage = new UsersPage();

    usersPage.logInButton.click();
    cy.get('#id_username').type(username);
    cy.get('#id_password').type(password);
    cy.get('.login-button').click();

    usersPage.logOutButton.should('be.visible');
    cy.url().then(currentUrl => {
      this.waitForPageToLoad(currentUrl.split('/').pop(), hasAccessRights);
    });

    if (!inAGP) {
      cy.wait('@datasets');
    }
  }

  public loginAdmin(inAGP = false): void {
    this.login(this.adminUsername, this.adminPassword, true, inAGP);
  }

  public logout(hasAccessRights = false): void {
    const usersPage = new UsersPage();

    usersPage.logOutButton.click();

    cy.location('pathname').should('eq', `/gpf/${toolPageLinks.home}`);
  }

  public navigateToDatasetPage(dataset: string, page: string, hasAccessRights = true): void {
    this.openDatasetsDropdownMenu();
    this.datasetsDropdownMenuElements.contains(dataset).should('be.visible').click({force: true});
    this.datasetsDropdownMenuButton.should('have.text', dataset);
    cy.get(`a.nav-link[href*="${page}"]`).click();

    this.waitForPageToLoad(page, hasAccessRights);
  }

  public waitForPageToLoad(page: string, hasAcessRights = true): void {
    if (hasAcessRights) {
      switch (page) {
        case toolPageLinks.datasetDescription:
          cy.get('gpf-dataset-description').should('be.visible');
          break;
        case toolPageLinks.datasetStatistics:
          cy.get('gpf-variant-reports').should('be.visible');
          break;
        case toolPageLinks.geneBrowser:
          cy.get('gpf-gene-browser').should('be.visible');
          break;
        case toolPageLinks.genotypeBrowser:
          cy.get('gpf-genotype-browser').should('be.visible');
          break;
        case toolPageLinks.phenotypeBrowser:
          cy.get('gpf-pheno-browser-table').should('be.visible');
          break;
        case toolPageLinks.phenotypeTool:
          cy.get('gpf-pheno-tool').should('be.visible');
          break;
        case toolPageLinks.enrichmentTool:
          cy.get('gpf-enrichment-tool').should('be.visible');
          break;
        case sidenavPageLinks.userProfile:
          cy.get('gpf-user-profile').should('be.visible');
          break;
        case sidenavPageLinks.geneProfiles:
          cy.get('.row-cell').eq(0).should('be.visible');
          break;
        case sidenavPageLinks.management:
          cy.get('gpf-user-management').eq(0).should('be.visible');
          break;
      }
    } else {
      cy.get('#permission-denied-prompt').should('be.visible');
    }
  }

  public get datasetsDropdownMenuButton(): element {
    return cy.get('#datasets-dropdown-menu-button');
  }

  public get datasetsDropdownMenuElements(): element {
    cy.get('.dataset-selector a').should('have.length', Object.keys(datasetIds).length);
    return cy.get('.dataset-selector a');
  }

  public openDatasetsDropdownMenu(): void {
    this.datasetsDropdownMenuButton.find('span').should('not.have.text', 'Loading datasets...');
    this.datasetsDropdownMenuButton.click();
    cy.get('.dataset-selector.dropdown-menu').should('have.class', 'show');
    cy.get('.dataset-selector a').should('have.length', Object.keys(datasetIds).length);
  }

  private get sidenavTogglerButton(): element {
    return cy.get('#sidenav-toggle-button');
  }

  public toggleSidenav(): void {
    this.sidenavTogglerButton.click();
    cy.wait(1000);
  }

  public prepareForVisualTest(): void {
    cy.get('html, body').invoke('attr', 'style', 'height: auto; scroll-behavior: auto;');
    // ?TODO: hide sticky table header; legend
  }

  public navigateToSidenavPage(sidenavPageLink: string): void {
    cy.get(`a[href="/gpf/${sidenavPageLink}"]`).click();
    this.waitForPageToLoad(sidenavPageLink);
  }

  public findButtonInComponentContainingText(componentSelector: string, text: string): element {
    if (text === '×') {
      return cy.get(componentSelector).contains('close');
    }
    return cy.get(componentSelector).contains(text);
  }

  public findErrorAlertInComponent(componentSelector: string): element {
    return cy.get(`${componentSelector} gpf-errors-alert .alert-danger`);
  }

  public findWarningAlertInComponent(componentSelector: string): element {
    return cy.get(`${componentSelector} .alert-warning`);
  }
}
