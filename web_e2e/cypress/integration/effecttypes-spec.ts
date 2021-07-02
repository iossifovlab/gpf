import { EffecttypesPage } from 'cypress/elements/effectypes-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Effect types tests', () => {
  const page = new EffecttypesPage();
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
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'None').click();
    page.findErrorAlertInComponent('gpf-effecttypes').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();
    page.findErrorAlertInComponent('gpf-effecttypes').should('not.exist');
  });

  it('should check/uncheck effect types checkboxes using \'All\' and \'None\' buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effecttypes').each((element) => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effecttypes').each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });
});
