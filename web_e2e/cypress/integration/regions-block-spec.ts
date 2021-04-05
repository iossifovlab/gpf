import { ErrorsAlertPage } from 'cypress/elements/errors-alert-page';
import { RegionsBlockPage } from 'cypress/elements/regions-block-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Regions block tests', () => {
  const regionsBlockPage = new RegionsBlockPage();

  before(() => {
    regionsBlockPage.navigateToHome();
    regionsBlockPage.loginAdmin();
  });

  after(() => {
    regionsBlockPage.logout();
  });

  beforeEach(() => {
    regionsBlockPage.navigateToHome();
  });

  it('should display regions filter panel', () => {
    regionsBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    regionsBlockPage.regionsFilterPanel.should('not.exist');

    regionsBlockPage.regionsFilterButton.click();
    regionsBlockPage.regionsFilterPanel.should('be.visible');
  });

  it('should display error alert in regions panel when the textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();
    regionsBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    regionsBlockPage.regionsFilterButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-regions-filter').should('be.visible');

    regionsBlockPage.regionsFilterTextarea.type('1:865582');
    errorsAlertPage.findAlertWindowInComponent('gpf-regions-filter').should('not.exist');
  });
});
