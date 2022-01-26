import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { datasetIds, sidenavPageLinks, toolPageLinks } from 'cypress/elements/utils';

describe('Save query tests', () => {
  const page = new SaveQueryPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should open save query dropdown menu after save query button click', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
  });

  it('should save a query, load it, open all tools tabs and delete the query', () => {
    const datasetsPage = new DatasetsPage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.button.click();
    page.dropdownNameInput.type('Test');
    page.saveButton.click();

    page.navigateToSidenavPage(sidenavPageLinks.savedQueries);
    page.tableFirstLoadButton.click();

    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.phenotypeToolButton.click();
    datasetsPage.geneBrowserButton.click();

    page.navigateToSidenavPage(sidenavPageLinks.savedQueries);
    page.tableFirstDeleteButton.click();
  });

  it('should navigate to genotype browser, check all effect types checkboxes, save a query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    page.button.click();
    page.dropdownNameInput.type('Test');
    page.saveButton.click();

    page.navigateToSidenavPage(sidenavPageLinks.savedQueries);
    page.tableFirstLoadButton.click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('be.checked');
    });

    page.navigateToSidenavPage(sidenavPageLinks.savedQueries);
    page.tableFirstDeleteButton.click();
  });
});
