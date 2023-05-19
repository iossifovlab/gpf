import { EffectTypesPage } from 'cypress/elements/effect-types-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Effect types tests', () => {
  const page = new EffectTypesPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'None').click();
    page.findErrorAlertInComponent('gpf-effect-types').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    page.findErrorAlertInComponent('gpf-effect-types').should('not.exist');
  });

  it('should check/uncheck effect types checkboxes using "All" and "None" buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('be.checked');
    });
  });
});
