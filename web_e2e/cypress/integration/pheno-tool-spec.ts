import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool tests', () => {
  const page = new PhenoToolPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    genesBlockPage.window.should('be.visible');
  });

  it('should display pheno tool measure block panel', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolMeasurePage.block.should('be.visible');
  });

  it('should display pheno tool genotye block panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.genotypeBlockPanel.should('be.visible');
  });

  it('should display family filters block panel', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display "Report" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.reportButton.should('be.visible');
  });

  it('should display "Share query" button', () => {
    const shareQueryPage = new ShareQueryPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    shareQueryPage.button.should('be.visible');
  });

  it('should display "Save query" button', () => {
    const saveQueryPage = new SaveQueryPage();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display "Download" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.visible');
  });

  it('should display pheno tool results chart after "Report" button click', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    page.resultsChart.should('not.exist');
    page.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    page.findButtonInComponentContainingText('gpf-searchable-select', 'i1.age').click();
    page.reportButton.click();
    page.resultsChart.should('be.visible');
  });
});
