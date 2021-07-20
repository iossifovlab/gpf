import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VarianttypesPage } from 'cypress/elements/varianttypes-page';

describe('Variant types tests', () => {
  const page = new VarianttypesPage();
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
    page.findErrorAlertInComponent('gpf-varianttypes').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'None').click();
    page.findErrorAlertInComponent('gpf-varianttypes').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-varianttypes', 'All').click();
    page.findErrorAlertInComponent('gpf-varianttypes').should('not.exist');
  });

  it('should check/uncheck variant types checkboxes using \'All\' and \'None\' buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
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
