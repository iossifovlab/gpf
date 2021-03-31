import { ErrorsAlertPage } from "cypress/elements/errors-alert-page";
import { PhenoToolMeasurePage } from "cypress/elements/pheno-tool-measure-page";
import { datasetIds, toolPageNames } from "cypress/elements/utils";

describe('Pheno tool measure tests', () => {
  const phenoToolMeasurePage = new PhenoToolMeasurePage();

  before(() => {
    phenoToolMeasurePage.navigateToHome();
    phenoToolMeasurePage.loginAdmin();
  });

  after(() => {
    phenoToolMeasurePage.logout();
  });

  beforeEach(() => {
    phenoToolMeasurePage.navigateToHome();
  });

  it('should display error alert when measure searchbox is empty', () => {
    const errorsAlertPage = new ErrorsAlertPage();
    phenoToolMeasurePage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    errorsAlertPage.findAlertWindowInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    phenoToolMeasurePage.findButtonInComponentContainingText('gpf-searchable-select', 'i1.age').click();
    errorsAlertPage.findAlertWindowInComponent('gpf-pheno-tool-measure').should('not.exist');
  });
});
