import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VarianttypesPage } from 'cypress/elements/varianttypes-page';

describe('Variant types tests', () => {
  const varianttypesPage = new VarianttypesPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    varianttypesPage.cleanup();
    varianttypesPage.navigateToHome();
    varianttypesPage.loginAdmin();
  });

  beforeEach(() => {
    varianttypesPage.preserveLogin();
    varianttypesPage.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    varianttypesPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    varianttypesPage.findErrorAlertInComponent('gpf-varianttypes').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None').click();
    varianttypesPage.findErrorAlertInComponent('gpf-varianttypes').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All').click();
    varianttypesPage.findErrorAlertInComponent('gpf-varianttypes').should('not.exist');
  });

  it('should check/uncheck variant types checkboxes using \'All\' and \'None\' buttons', () => {
    varianttypesPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-varianttypes').each((element) => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-varianttypes').each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });
});
