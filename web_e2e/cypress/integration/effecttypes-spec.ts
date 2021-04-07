import { EffecttypesPage } from 'cypress/elements/effectypes-page';
import { ErrorsAlertPage } from 'cypress/elements/errors-alert-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Effect types tests', () => {
  const effecttypesPage = new EffecttypesPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    effecttypesPage.cleanup();
    effecttypesPage.navigateToHome();
    effecttypesPage.loginAdmin();
  });

  beforeEach(() => {
    effecttypesPage.preserveLogin();
    effecttypesPage.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    const errorsAlertPage = new ErrorsAlertPage();

    effecttypesPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'None').click();
    errorsAlertPage.findAlertWindowInComponent('gpf-effecttypes').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();
    errorsAlertPage.findAlertWindowInComponent('gpf-effecttypes').should('not.exist');
  });

  it('should check/uncheck effect types checkboxes using \'All\' and \'None\' buttons', () => {
    effecttypesPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
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
