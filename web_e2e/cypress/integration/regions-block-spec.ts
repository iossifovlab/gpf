import { RegionsBlockPage } from 'cypress/elements/regions-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Regions block tests', () => {
  const regionsBlockPage = new RegionsBlockPage();

  before(() => {
    regionsBlockPage.cleanup();
    regionsBlockPage.navigateToHome();
    regionsBlockPage.loginAdmin();
  });

  beforeEach(() => {
    regionsBlockPage.preserveLogin();
    regionsBlockPage.navigateToHome();
  });

  it('should display regions filter panel', () => {
    regionsBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    regionsBlockPage.regionsFilterPanel.should('not.exist');

    regionsBlockPage.regionsFilterButton.click();
    regionsBlockPage.regionsFilterPanel.should('be.visible');
  });

  it('should display error alert in regions panel when the textarea is empty', () => {
    regionsBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    regionsBlockPage.regionsFilterButton.click();
    regionsBlockPage.findErrorAlertInComponent('gpf-regions-filter').should('be.visible');

    regionsBlockPage.regionsFilterTextarea.type('1:865582');
    regionsBlockPage.findErrorAlertInComponent('gpf-regions-filter').should('not.exist');
  });
});
