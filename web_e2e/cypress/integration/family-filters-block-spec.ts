import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Family filters block tests', () => {
  const page = new FamilyFilterBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display family ids panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.familyIdsPanel.should('not.exist');

    page.familyIdsButton.click();
    page.familyIdsPanel.should('be.visible');
  });

  it('should display error alert in family ids panel when the textarea is empty', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);

    page.familyIdsButton.click();
    page.findErrorAlertInComponent('gpf-family-ids').should('be.visible');

    page.familyIdsTextarea.type('f1');
    page.findErrorAlertInComponent('gpf-family-ids').should('not.exist');
  });

  it('should display pheno filters panel after "Advanced" button click', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.phenoFiltersPanel.should('not.exist');

    page.advancedButton.click();
    page.phenoFiltersPanel.should('be.visible');

    page.allButton.click();
    page.phenoFiltersPanel.should('not.exist');
  });
});
