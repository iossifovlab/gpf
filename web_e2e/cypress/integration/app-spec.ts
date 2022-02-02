import { AppPage } from 'cypress/elements/app-page';
import { DatasetsPage } from 'cypress/elements/datasets-page';
import { UserManagementPage } from 'cypress/elements/user-management-page';
import { datasetIds, sidenavPageLinks, toolPageLinks, userData } from 'cypress/elements/utils';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

describe('App tests', () => {
  const page = new AppPage();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
  });

  it.only('should display "GPF: Genotypes and Phenotypes in Families" as a title', () => {
    page.loginAdmin();
    page.title.should('have.text', 'GPF: Genotypes and Phenotypes in Families');
    page.logout();
  });

  it('should toggle sidenav, click on the "Datasets" button and ' +
     'navigate to "/datasets/ALL_genotypes/gene-browser"', () => {
    const baseUrl = Cypress.config().baseUrl;
    const expectedUrl = `${baseUrl}datasets/ALL_genotypes/${toolPageLinks.geneBrowser}`;

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.datasets);

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(expectedUrl);
    });

    page.logout();
  });

  it('should toggle sidenav, click on the "Saved queries" button and navigate to "/saved-queries"', () => {
    const baseUrl = Cypress.config().baseUrl;
    const savedQueriesUrl = `${baseUrl}saved-queries`;

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.savedQueries);

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(savedQueriesUrl);
    });

    page.logout();
  });

  it('should toggle sidenav, click on the "Management" button and navigate to "/management"', () => {
    const baseUrl = Cypress.config().baseUrl;
    const managementUrl = `${baseUrl}management`;

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(managementUrl);
    });

    page.logout();
  });

  it('should toggle sidenav, click on the "Autism gene profiles" button and ' +
     'navigate to "/autism-gene-profiles"', () => {
    const baseUrl = Cypress.config().baseUrl;
    const autismGeneProfilesUrl = `${baseUrl}autism-gene-profiles`;

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);

    cy.url().then(currentUrl => {
      expect(currentUrl).to.eq(autismGeneProfilesUrl);
    });

    page.logout();
  });
});

describe('App user access rights tests', () => {
  const page = new AppPage();
  const datasetsPage = new DatasetsPage();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
  });

  Object.values(userData).forEach(data => {
    it('should toggle sidenav bar with the right elements inside', () => {
      page.login(data.username, data.password);
      page.sidenavElements.should('not.exist');

      page.toggleSidenav();
      page.sidenavElements.should('have.length', data.sidenavElementsCount);

      page.toggleSidenav();
      page.sidenavElements.should('not.exist');

      if (data.username || data.password !== undefined) {
        page.logout();
      }
    });
  });

  it('should go through all tools and check whether the permission denied prompt ' +
     'is displayed when not logged in and not displayed when logged in with admin account', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
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
    page.logout();
  });

  Object.values(userData).forEach(data => {
    it('should login with accounts with different access rights and check whether the datasets ' +
       'in the dropdown have the correct opacity value', () => {
      const expectedOpacity = data.hasDatasetRights ? '1' : '0.3';

      page.login(data.username, data.password);
      page.openDatasetsDropdownMenu();
      page.datasetsDropdownMenuElements.each(ele => cy.wrap(ele).should('have.css', 'opacity', expectedOpacity));

      if (data.username || data.password !== undefined) {
        page.logout();
      }
    });
  });

  it.only('should validate that researcher has no rights', () => {
    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    page.login(userData.normal.username, userData.normal.password);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    page.logout();
  });

  it.only('should login admin and give researcher access rights for comp_vcf, ' +
     'then login researcher and verify his rights', () => {
    const userManagementPage = new UserManagementPage();

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.allUserEditGroupRemoveButtons.should('be.visible');
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropDownMenuButton.should('be.visible');
    userManagementPage.userWindowGroupDropdownSearch.type('comp_vcf');
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();
    page.logout();

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    page.login(userData.normal.username, userData.normal.password);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.logout();
  });

  it.only('should login admin and give researcher access rights for COMP_genotypes, ' +
     'then login researcher and verify his rights', () => {
    const userManagementPage = new UserManagementPage();
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.allUserEditGroupRemoveButtons.should('be.visible');
    userManagementPage.allUserEditGroupRemoveButtons.click({multiple: true})  ;
    userManagementPage.userWindowGroupDropDownMenuButton.should('be.visible');
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownSearch.type('COMP_genotypes');
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();
    page.logout();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
    page.login(userData.normal.username, userData.normal.password);
    datasetsPage.permissionDeniedPrompt.should('exist');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.allGenotypes, toolPageLinks.genotypeBrowser);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    genotypeBrowserPage.window.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.genotypeBrowser);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    genotypeBrowserPage.window.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compDenovo, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.multi, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.logout();
  });

  it.only('should login admin and give researcher access rights for ALL Genotypes, ' +
     'then login researcher and verify his rights', () => {
    const userManagementPage = new UserManagementPage();
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.allUserEditGroupRemoveButtons.click({multiple: true});
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownSearch.type('ALL_Genotypes');
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();
    page.logout();

    page.navigateToDatasetPage(datasetIds.allGenotypes, toolPageLinks.genotypeBrowser);
    page.login(userData.normal.username, userData.normal.password);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    genotypeBrowserPage.window.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.genotypeBrowser);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    genotypeBrowserPage.window.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compDenovo, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.navigateToDatasetPage(datasetIds.multi, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('not.exist');
    datasetsPage.datasetStatisticsWindow.should('be.visible');

    page.logout();
  });

  it.only('should login admin and remove all researcher access rights, then login researcher and verify his rights', () => {
    const userManagementPage = new UserManagementPage();
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management); 
    userManagementPage.getUserEditorButtonByEmail(userData.normal.username).click();
    userManagementPage.allUserEditGroupRemoveButtons.click({multiple: true});
    userManagementPage.userWindowSubmitButton.click();
    page.logout();

    page.navigateToDatasetPage(datasetIds.allGenotypes, toolPageLinks.genotypeBrowser);
    page.login(userData.normal.username, userData.normal.password);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    genotypeBrowserPage.window.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.genotypeBrowser);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    genotypeBrowserPage.window.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compDenovo, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compVcf, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.navigateToDatasetPage(datasetIds.multi, toolPageLinks.datasetStatistics);
    datasetsPage.permissionDeniedPrompt.should('be.visible');
    datasetsPage.datasetStatisticsWindow.should('not.exist');

    page.logout();
  });
});
