import { FamilyFilterBlockPage } from 'cypress/elements/family-filter-block-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { PhenoToolMeasurePage } from 'cypress/elements/pheno-tool-measure-page';
import { PhenoToolPage } from 'cypress/elements/pheno-tool-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Pheno tool tests', () => {
  const phenoToolPage = new PhenoToolPage();

  before(() => {
    phenoToolPage.navigateToHome();
    phenoToolPage.loginAdmin();
  });

  after(() => {
    phenoToolPage.logout();
  });

  beforeEach(() => {
    phenoToolPage.navigateToHome();
  });

  it('should display genes block panel', () => {
    const genesBlockPage = new GenesBlockPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    genesBlockPage.window.should('be.visible');
  });

  it('should display pheno tool measure block panel', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    phenoToolMeasurePage.block.should('be.visible');
  });

  it('should display pheno tool genotye block panel', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    phenoToolPage.genotypeBlockPanel.should('be.visible');
  });

  it('should display family filters block panel', () => {
    const familyFilterBlockPage = new FamilyFilterBlockPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    familyFilterBlockPage.window.should('be.visible');
  });

  it('should display \'Report\' button', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    phenoToolPage.reportButton.should('be.visible');
  });

  it('should display \'Share query\' button', () => {
    const shareQueryPage = new ShareQueryPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    shareQueryPage.button.should('be.visible');
  });

  it('should display \'Save query\' button', () => {
    const saveQueryPage = new SaveQueryPage();
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    saveQueryPage.button.should('be.visible');
  });

  it('should display \'Download\' button', () => {
    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    phenoToolPage.findButtonInComponentContainingText('gpf-pheno-tool', 'Download').should('be.visible');
  });

  it('should display pheno tool results chart after \'Report\' button click', () => {
    const phenoToolMeasurePage = new PhenoToolMeasurePage();

    phenoToolPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeTool);
    phenoToolPage.resultsChart.should('not.exist');

    phenoToolMeasurePage.searchbox.click();
    phenoToolPage.findButtonInComponentContainingText('gpf-searchable-select', 'i1.age').click();
    phenoToolPage.reportButton.click();
    phenoToolPage.resultsChart.should('be.visible');
  });
});
