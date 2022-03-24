import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool measure tests', () => {
  const page = new PhenoToolMeasurePage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display error alert when measure searchbox is empty', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('not.exist');
  });
});
