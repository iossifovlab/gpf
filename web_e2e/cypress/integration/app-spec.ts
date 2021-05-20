import { AppPage } from 'cypress/elements/app-page';
import { DatasetsPage } from 'cypress/elements/datasets-page';
import { toolPageLinks, userData } from 'cypress/elements/utils';

describe('App tests', () => {
  const appPage = new AppPage();

  before(() => {
    appPage.cleanup();
  });

  beforeEach(() => {
    appPage.navigateToHome();
  });

  it('should display \'GPF: Genotypes and Phenotypes in Families\' as a title', () => {
    appPage.loginAdmin();
    appPage.title.should('have.text', 'GPF: Genotypes and Phenotypes in Families');
    appPage.logout();
  });

  it('should toggle sidenav, click on the \'Datasets\' button and navigate to \'/datasets/ALL_genotypes/genotype-browser\'', () => {
    const baseUrl = Cypress.config().baseUrl;
    const expectedUrl = `${baseUrl}datasets/ALL_genotypes/${toolPageLinks.genotypeBrowser}`;

    appPage.loginAdmin();
    appPage.toggleSidenav();
    appPage.sidenavDatasetButton.click();

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(expectedUrl);
    });

    appPage.logout();
  });

  it('should toggle sidenav, click on the \'Saved queries\' button and navigate to \'/saved-queries\'', () => {
    const baseUrl = Cypress.config().baseUrl;
    const savedQueriesUrl = `${baseUrl}saved-queries`;

    appPage.loginAdmin();
    appPage.toggleSidenav();
    appPage.sidenavSavedQueriesButton.click();

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(savedQueriesUrl);
    });

    appPage.logout();
  });

  it('should toggle sidenav, click on the \'Management\' button and navigate to \'/management\'', () => {
    const baseUrl = Cypress.config().baseUrl;
    const managementUrl = `${baseUrl}management`;

    appPage.loginAdmin();
    appPage.toggleSidenav();
    appPage.sidenavManagementButton.click();

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(managementUrl);
    });

    appPage.logout();
  });

  it('should toggle sidenav, click on the \'Autism gene profiles\' button and navigate to \'/autism-gene-profiles\'', () => {
    const baseUrl = Cypress.config().baseUrl;
    const autismGeneProfilesUrl = `${baseUrl}autism-gene-profiles`;

    appPage.loginAdmin();
    appPage.toggleSidenav();
    appPage.sidenavAutismGeneProfilesButton.click();

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(autismGeneProfilesUrl);
    });

    appPage.logout();
  });
});

describe('User access rights tests', () => {
  const appPage = new AppPage();
  const datasetsPage = new DatasetsPage();

  before(() => {
    appPage.cleanup();
  });

  beforeEach(() => {
    appPage.navigateToHome();
  });

  Object.values(userData).forEach((data) => {
    it('should toggle sidenav bar with the right elements inside', () => {
      appPage.login(data['username'], data['password']);
      appPage.sidenavElements.should('not.exist');

      appPage.toggleSidenav();
      appPage.sidenavElements.should('have.length', data['sidenavElementsCount']);

      appPage.toggleSidenav();
      appPage.sidenavElements.should('not.exist');

      if (data['username'] || data['password'] !== undefined) {
        appPage.logout();
      }
    });
  });

  it('should go through all tools and check whether the permission denied prompt ' +
     'is displayed when not logged in and not displayed when logged in with admin account', () => {
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.geneBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.phenotypeToolButton.click();
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.permissionDeniedPrompt.should('be.visible');

    datasetsPage.loginAdmin();
    datasetsPage.permissionDeniedPrompt.should('not.exist');

    datasetsPage.geneBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('not.exist');

    datasetsPage.phenotypeToolButton.click();
    datasetsPage.permissionDeniedPrompt.should('not.exist');

    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('not.exist');

    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.permissionDeniedPrompt.should('not.exist');

    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    appPage.logout();
  });

  Object.values(userData).forEach((data) => {
    it('should login with accounts with different access rights and check whether the datasets ' +
       'in the dropdown have the correct opacity value', () => {
      const expectedOpacity = data['hasDatasetRights'] ? '1' : '0.3';

      appPage.login(data['username'], data['password']);
      datasetsPage.datasetsDropdownMenuButton.click();
      cy.wait(1000);
      datasetsPage.datasetsDropdownMenuElements.each(ele => cy.wrap(ele).should('have.css', 'opacity', expectedOpacity));

      if (data['username'] || data['password'] !== undefined) {
        appPage.logout();
      }
    });
  });
});
