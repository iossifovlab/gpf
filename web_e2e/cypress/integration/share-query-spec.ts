import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

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
  });

  it('should open share query dropdown menu after share query button click', () => {
    shareQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    shareQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    shareQueryPage.button.click();
    shareQueryPage.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');
  });

  it('should share a query, load it and open all tools tabs', () => {
    const datasetsPage = new DatasetsPage();

    shareQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    shareQueryPage.button.click();
    shareQueryPage.input.invoke('val').then((url) => {
      cy.visit(String(url));
      datasetsPage.datasetStatisticsButton.click();
      datasetsPage.genotypeBrowserButton.click();
      datasetsPage.phenotypeBrowserButton.click();
      datasetsPage.phenotypeToolButton.click();
    })
  });

  it('should navigate to genotype browser, check all effect types checkboxes, generate a share query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    shareQueryPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effecttypes', 'All').click();

    shareQueryPage.button.click();
    shareQueryPage.input.invoke('val').then((url) => {
      cy.visit(String(url));
      genotypeBlockPage.findAllCheckboxesInComponent('gpf-effecttypes').each((element) => {
        cy.wrap(element).should('be.checked');
      });
    })
  });
});
