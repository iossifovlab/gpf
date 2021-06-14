import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { PedigreeSelectorPage } from 'cypress/elements/pedigree-selector-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pedigree selector tests', () => {
  const pedigreeSelectorPage = new PedigreeSelectorPage();
  const genotypeBlockPage = new GenotypeBlockPage();

  before(() => {
    pedigreeSelectorPage.cleanup();
    pedigreeSelectorPage.navigateToHome();
    pedigreeSelectorPage.loginAdmin();
  });

  beforeEach(() => {
    pedigreeSelectorPage.preserveLogin();
    pedigreeSelectorPage.navigateToHome();
  });

  it('should display error alert when none of the checkboxes are selected', () => {
    pedigreeSelectorPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    pedigreeSelectorPage.findErrorAlertInComponent('gpf-pedigree-selector').should('not.exist');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
    pedigreeSelectorPage.findErrorAlertInComponent('gpf-pedigree-selector').should('be.visible');

    genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
    pedigreeSelectorPage.findErrorAlertInComponent('gpf-pedigree-selector').should('not.exist');
  });

  it('should check/uncheck affected status checkboxes using \'All\' and \'None\' buttons', () => {
    pedigreeSelectorPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'None').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-pedigree-selector').each((element) => {
      cy.wrap(element).should('not.be.checked');
    });

    genotypeBlockPage.findButtonInComponentContainingText('gpf-pedigree-selector', 'All').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-pedigree-selector').each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });
});
