import { GenderPage } from 'cypress/elements/gender-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gender tests', () => {
  const page = new GenderPage();
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
    page.findErrorAlertInComponent('gpf-gender').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();
    page.findErrorAlertInComponent('gpf-gender').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();
    page.findErrorAlertInComponent('gpf-gender').should('not.exist');
  });

  it('should check/uncheck child gender checkboxes using \'All\' and \'None\' buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-gender').each((element) => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-gender').each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });
});
