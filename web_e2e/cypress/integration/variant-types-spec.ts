import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { VariantTypesPage } from 'cypress/elements/variant-types-page';

describe('Variant types tests', () => {
  const page = new VariantTypesPage();
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
    page.findErrorAlertInComponent('gpf-variant-types').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'None').click();
    page.findErrorAlertInComponent('gpf-variant-types').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'All').click();
    page.findErrorAlertInComponent('gpf-variant-types').should('not.exist');
  });

  it('should check/uncheck variant types checkboxes using "All" and "None" buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-variant-types').each(element => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-variant-types', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-variant-types').each(element => {
      cy.wrap(element).should('be.checked');
    });
  });
});
