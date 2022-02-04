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

  public navigateToHome(waitForPage = true): void {
    let baseUrl = Cypress.config().baseUrl;
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1);
    }

    cy.visit(`${baseUrl}/datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`);

    if (waitForPage) {
      this.waitForPage(toolPageLinks.geneBrowser);
    } else {
      this.waitForPremissionDeniedPrompt();
    }
  }

  public login(username: string, password: string, waitForPage = true): void {
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

    if (waitForPage) {
      cy.url().then(currentUrl => {
        this.waitForPage(currentUrl.split('/').pop())
      });
    } else {
      this.waitForPremissionDeniedPrompt();
    }
  }

  public loginAdmin(): void {
    this.login(this.adminUsername, this.adminPassword);
  }

  public logout(): void {
    const usersPage = new UsersPage();
    usersPage.logoutButton.click();
    usersPage.loginDropdownToggleButton.should('be.visible');
  }

  public navigateToDatasetPage(dataset: string, page: string, waitForPage = true): void {
    this.openDatasetsDropdownMenu();
    this.datasetsDropdownMenuElements.contains(dataset).click();
    this.datasetsDropdownMenuButton.should('have.text', dataset);
    cy.get(`a.nav-link[href*="${page}"]`).click();

    if (waitForPage) {
      this.waitForPage(page);
    } else {
      this.waitForPremissionDeniedPrompt();
    }
  }

  private waitForPage(page: string): void {
    switch(page) {
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
      case sidenavPageLinks.savedQueries:
        cy.get('gpf-saved-queries').should('be.visible');
        break;
      case sidenavPageLinks.autismGeneProfiles:
        cy.get('.row-cell').eq(0).should('be.visible');
        break;
      case sidenavPageLinks.management:
        cy.get('gpf-table-view-cell').eq(0).should('be.visible');
        break;
    }
  }

  private waitForPremissionDeniedPrompt(): void {
    cy.get('#permission-denied-prompt').should('be.visible');
  }

  public get datasetsDropdownMenuButton(): element {
    cy.get('#datasets-dropdown-menu-button').should('be.visible'); // useful?
    return cy.get('#datasets-dropdown-menu-button');
  }

  public get datasetsDropdownMenuElements(): element {
    cy.get('.dataset-selector a').should('have.length', Object.keys(datasetIds).length)
    return cy.get('.dataset-selector a');
  }

  public openDatasetsDropdownMenu(): void {
    this.datasetsDropdownMenuButton.click();
    cy.get('.dataset-selector.dropdown-menu').should('have.class', 'show');
  }

  private get sidenavTogglerButton(): element {
    return cy.get('.navbar-toggler-icon');
  }

  public toggleSidenav(): void {
    this.sidenavTogglerButton.click({scrollBehavior: false});
  }

  public navigateToSidenavPage(sidenavPageLink: string, waitForPage = true): void {
    this.sidenavTogglerButton.scrollIntoView();
    this.toggleSidenav();
    cy.get(`div.sidenav a[routerlink="/${sidenavPageLink}"]`).click({scrollBehavior: false});

    if (waitForPage) {
      this.waitForPage(sidenavPageLink.split('/').pop());
    }
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
