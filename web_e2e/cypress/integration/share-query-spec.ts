import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Share query tests', () => {
  const page = new ShareQueryPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
  });

  it('should open share query dropdown menu after share query button click', () => {
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');
  });

  it('should share a query, load it and open all tools tabs', () => {
    const datasetsPage = new DatasetsPage();

    page.button.click();
    page.input.invoke('val').then((url) => {
      cy.visit(String(url)).then(() => {
        datasetsPage.datasetStatisticsButton.click();
        datasetsPage.genotypeBrowserButton.click();
        datasetsPage.phenotypeBrowserButton.click();
        datasetsPage.phenotypeToolButton.click();
        datasetsPage.geneBrowserButton.click();
      });
    })
  });

  it('should navigate to genotype browser, check all effect types checkboxes, generate a share query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();

    page.button.click();
    page.input.invoke('val').then((url) => {
      cy.visit(String(url)).then(() => {
        genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each((element) => {
          cy.wrap(element).should('be.checked');
        });
      })
    })
  });
});
