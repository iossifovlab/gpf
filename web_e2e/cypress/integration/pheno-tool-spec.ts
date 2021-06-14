import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno tool tests', () => {
  const phenoToolPage = new PhenoToolPage();

  before(() => {
    phenoToolPage.cleanup();
    phenoToolPage.navigateToHome();
    phenoToolPage.loginAdmin();
  });

  beforeEach(() => {
    phenoToolPage.preserveLogin();
    phenoToolPage.navigateToHome();
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    genesBlockPage.window.should('be.visible');
  });

  it('should display pheno tool measure block panel', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolMeasurePage.block.should('be.visible');
  });

  it('should display pheno tool genotye block panel', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolPage.genotypeBlockPanel.should('be.visible');
  });

  it('should display family filters block panel', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display \'Report\' button', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolPage.reportButton.should('be.visible');
  });

  it('should display \'Share query\' button', () => {
    const shareQueryPage = new ShareQueryPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    shareQueryPage.button.should('be.visible');
  });

  it('should display \'Save query\' button', () => {
    const saveQueryPage = new SaveQueryPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display \'Download\' button', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolPage.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.visible');
  });

  it('should display pheno tool results chart after \'Report\' button click', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeTool);
    phenoToolPage.resultsChart.should('not.exist');
    phenoToolPage.findErrorAlertInComponent('gpf-pheno-tool-measure').should('be.visible');

    phenoToolMeasurePage.searchbox.click();
    phenoToolPage.findButtonInComponentContainingText('gpf-searchable-select', 'i1.age').click();
    phenoToolPage.reportButton.click();
    phenoToolPage.resultsChart.should('be.visible');
  });
});
