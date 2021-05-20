import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Share query tests', () => {
  const shareQueryPage = new ShareQueryPage();

  before(() => {
    shareQueryPage.cleanup();
    shareQueryPage.navigateToHome();
    shareQueryPage.loginAdmin();
  });

  beforeEach(() => {
    shareQueryPage.preserveLogin();
    shareQueryPage.navigateToHome();
    shareQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
  });

  it('should open share query dropdown menu after share query button click', () => {
    shareQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    shareQueryPage.button.click();
    shareQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');
  });

  it('should share a query, load it and open all tools tabs', () => {
    const datasetsPage = new DatasetsPage();

    shareQueryPage.button.click();
    shareQueryPage.input.invoke('val').then((url) => {
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

    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();

    shareQueryPage.button.click();
    shareQueryPage.input.invoke('val').then((url) => {
      cy.visit(String(url)).then(() => {
        genotypeBlockPage.findAllCheckboxesInComponent('gpf-effecttypes').each((element) => {
          cy.wrap(element).should('be.checked');
        });
      })
    })
  });
});
