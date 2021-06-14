import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool measure tests', () => {
  const phenoToolMeasurePage = new PhenoToolMeasurePage();

  before(() => {
    phenoToolMeasurePage.cleanup();
    phenoToolMeasurePage.navigateToHome();
    phenoToolMeasurePage.loginAdmin();
  });

  beforeEach(() => {
    phenoToolMeasurePage.preserveLogin();
    phenoToolMeasurePage.navigateToHome();
  });

  it('should display error alert when measure searchbox is empty', () => {
    phenoToolMeasurePage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolMeasurePage.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.findButtonInComponentContainingText('gpf-searchable-select', 'i1.age').click();
    phenoToolMeasurePage.findErrorAlertInComponent('gpf-pheno-tool-measure').should('not.exist');
  });
});
