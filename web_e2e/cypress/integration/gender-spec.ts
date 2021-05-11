import { GenderPage } from 'cypress/elements/gender-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gender tests', () => {
  const genderPage = new GenderPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    genderPage.cleanup();
    genderPage.navigateToHome();
    genderPage.loginAdmin();
  });

  beforeEach(() => {
    genderPage.preserveLogin();
    genderPage.navigateToHome();
  });

  // review
  // see if u can add error alert window as a var before everything
  it('should display error alert when none of the checkboxes are selected', () => {
    genderPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genderPage.findErrorAlertInComponent('gpf-gender').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'None').click();
    genderPage.findErrorAlertInComponent('gpf-gender').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-gender', 'All').click();
    genderPage.findErrorAlertInComponent('gpf-gender').should('not.exist');
  });

  it('should check/uncheck child gender checkboxes using \'All\' and \'None\' buttons', () => {
    genderPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
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
