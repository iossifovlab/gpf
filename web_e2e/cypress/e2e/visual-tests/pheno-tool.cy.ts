import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool visual tests', () => {
  const phenoToolPage = new PhenoToolPage();
  const phenoToolMeasurePage = new PhenoToolMeasurePage();
  before(() => {
    phenoToolPage.cleanup();
    phenoToolPage.navigateToHome(false);
    phenoToolPage.loginAdmin();
  });

  beforeEach(() => {
    phenoToolPage.preserveLogin();
    phenoToolPage.navigateToHome();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolPage.prepareForVisualTest();
  });

  it('should check the pheno tool with clear state', () => {
    cy.matchImage();
  });

  [
    {measure: 'i1.age', normalizedBy: []},
    {measure: 'i1.iq', normalizedBy: []},
    {measure: 'i1.m1', normalizedBy: []},
    {measure: 'i1.m2', normalizedBy: ['Age']},
    {measure: 'i1.m3', normalizedBy: ['Non verbal IQ']},
    {measure: 'i1.m4', normalizedBy: ['Age', 'Non verbal IQ']}
  ].forEach(data => {
    it('should check report with measure ' + data.measure + ' and normalization ' + String(data.normalizedBy), () => {
      phenoToolMeasurePage.searchbox.click();
      phenoToolMeasurePage.getDropdownOptionByText(data.measure).click();

      if (data.normalizedBy.length) {
        data.normalizedBy.forEach(checkbox => phenoToolMeasurePage.getCheckboxByText(checkbox).click());
      }

      phenoToolPage.pressReportButton();
      phenoToolPage.resultsChart.should('be.visible');
      cy.matchImage();
    });
  });
});