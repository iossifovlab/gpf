import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { InheritancetypesPage } from 'cypress/elements/inheritancetypes-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Inheritance tests', () => {
  const page = new InheritancetypesPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.findErrorAlertInComponent('gpf-inheritancetypes').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None').click();
    page.findErrorAlertInComponent('gpf-inheritancetypes').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All').click();
    page.findErrorAlertInComponent('gpf-inheritancetypes').should('not.exist');
  });

  it('should check/uncheck effect types checkboxes using "All" and "None" buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-inheritancetypes').each((element) => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-inheritancetypes', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-inheritancetypes').each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });
});
