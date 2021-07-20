import { RegionsBlockPage } from 'cypress/elements/regions-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Regions block tests', () => {
  const page = new RegionsBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display regions filter panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.regionsFilterPanel.should('not.exist');

    page.regionsFilterButton.click();
    page.regionsFilterPanel.should('be.visible');
  });

  it('should display error alert in regions panel when the textarea is empty', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.regionsFilterButton.click();
    page.findErrorAlertInComponent('gpf-regions-filter').should('be.visible');

    page.regionsFilterTextarea.type('1:865582');
    page.findErrorAlertInComponent('gpf-regions-filter').should('not.exist');
  });
});
