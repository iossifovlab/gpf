import { ErrorsAlertPage } from 'cypress/elements/errors-alert-page';
import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Family filters block tests', () => {
  const familyFilterBlockPage = new FamilyFilterBlockPage();

  before(() => {
    familyFilterBlockPage.navigateToHome();
    familyFilterBlockPage.loginAdmin();
  });

  after(() => {
    familyFilterBlockPage.logout();
  });

  beforeEach(() => {
    familyFilterBlockPage.navigateToHome();
  });

  it('should display family ids panel', () => {
    familyFilterBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    familyFilterBlockPage.familyIdsPanel.should('not.exist');

    familyFilterBlockPage.familyIdsButton.click();
    familyFilterBlockPage.familyIdsPanel.should('be.visible');
  });

  it('should display error alert in family ids panel when the textarea is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();
    familyFilterBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);

    familyFilterBlockPage.familyIdsButton.click();
    errorsAlertPage.findAlertWindowInComponent('gpf-family-ids').should('be.visible');

    familyFilterBlockPage.familyIdsTextarea.type('f1');
    errorsAlertPage.findAlertWindowInComponent('gpf-family-ids').should('not.exist');

  });

  it('should display pheno filters panel after \'Advanced\' button click', () => {
    familyFilterBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    familyFilterBlockPage.phenoFiltersPanel.should('not.exist');

    familyFilterBlockPage.advancedButton.click();
    familyFilterBlockPage.phenoFiltersPanel.should('be.visible');
  });

//   Uncomment me when NgbNav no longer always show dropdown menu
//   it('should stop displaying tab panel after \'All\' button click', () => {
//     familyFilterBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
//     familyFilterBlockPage.tabPanel.should('not.exist');

//     familyFilterBlockPage.familyIdsButton.click();
//     familyFilterBlockPage.tabPanel.should('be.visible');

//     familyFilterBlockPage.allButton.click();
//     familyFilterBlockPage.tabPanel.should('not.exist');
//   });
});
