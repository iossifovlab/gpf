import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Save query tests', () => {
  const saveQueryPage = new SaveQueryPage();

  before(() => {
    saveQueryPage.navigateToHome();
    saveQueryPage.loginAdmin();
  });

  after(() => {
    saveQueryPage.logout();
  });

  beforeEach(() => {
    saveQueryPage.navigateToHome();
    Cypress.Cookies.preserveOnce('sessionid');
  });

  it('should open save query dropdown menu after save query button click', () => {
    saveQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    saveQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    saveQueryPage.button.click();
    saveQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
  });

  it('should save a query, load it, open all tools tabs and delete the query', () => {
    const datasetsPage = new DatasetsPage();

    saveQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    saveQueryPage.button.click();
    saveQueryPage.dropdownNameInput.type('Test');
    saveQueryPage.saveButton.click();

    saveQueryPage.toggleSidenav();
    saveQueryPage.sidenavSavedQueriesButton.click();
    saveQueryPage.tableFirstLoadButton.click();

    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.phenotypeToolButton.click();

    saveQueryPage.toggleSidenav();
    saveQueryPage.sidenavSavedQueriesButton.click();
    saveQueryPage.tableFirstDeleteButton.click();
  });

  it('should navigate to genotype browser, check all effect types checkboxes, save a query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    saveQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();
    saveQueryPage.button.click();
    saveQueryPage.dropdownNameInput.type('Test');
    saveQueryPage.saveButton.click();

    saveQueryPage.toggleSidenav();
    saveQueryPage.sidenavSavedQueriesButton.click();
    saveQueryPage.tableFirstLoadButton.click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effecttypes').each((element) => {
      cy.wrap(element).should('be.checked');
    });

    saveQueryPage.toggleSidenav();
    saveQueryPage.sidenavSavedQueriesButton.click();
    saveQueryPage.tableFirstDeleteButton.click();
  });
});
