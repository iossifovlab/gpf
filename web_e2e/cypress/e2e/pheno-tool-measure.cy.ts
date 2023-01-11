import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool measure tests', () => {
  const page = new PhenoToolMeasurePage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
  });

  it('should display error alert when measure searchbox is empty', () => {
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('not.exist');
  });

  it('should check if Age checkbox is disabled', () => {
    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.age').click();
    page.block.contains('Age').find('input[type="checkbox"]').should('be.disabled');
  });

  it('should check if Non verbal IQ checkbox is disabled', () => {
    page.searchbox.click();
    page.findButtonInComponentContainingText('gpf-pheno-measure-selector', 'i1.iq').click();
    page.block.contains('Non verbal IQ').find('input[type="checkbox"]').should('be.disabled');
  });
});
