import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GeneViewPage } from 'cypress/elements/gene-view-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene view tests', () => {
  const geneViewPage = new GeneViewPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    geneViewPage.cleanup();
    geneViewPage.navigateToHome();
    geneViewPage.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  it('should have Affected status checkboxes', () => {
    geneViewPage.getAffectedStatusCheckbox('Affected only').should('be.visible');
    geneViewPage.getAffectedStatusCheckbox('Unaffected only').should('be.visible');
    geneViewPage.getAffectedStatusCheckbox('Affected and unaffected').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneViewPage.getEffectTypesCheckbox('LGDs').should('be.visible');
    geneViewPage.getEffectTypesCheckbox('Missense').should('be.visible');
    geneViewPage.getEffectTypesCheckbox('Synonymous').should('be.visible');
    geneViewPage.getEffectTypesCheckbox('CNV+').should('be.visible');
    geneViewPage.getEffectTypesCheckbox('CNV-').should('be.visible');
    geneViewPage.getEffectTypesCheckbox('Other').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneViewPage.getInheritanceTypes('Denovo').should('be.visible');
    geneViewPage.getInheritanceTypes('Transmitted').should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    geneViewPage.getVariantTypes('del').should('be.visible');
    geneViewPage.getVariantTypes('ins').should('be.visible');
    geneViewPage.getVariantTypes('del').should('be.visible');
    geneViewPage.getVariantTypes('CNV+').should('be.visible');
    geneViewPage.getVariantTypes('CNV-').should('be.visible');
  });

  it('should have undo button', () => {
    geneViewPage.undoButton.should('be.visible');
  });

  it('should have redo button', () => {
    geneViewPage.redoButton.should('be.visible');
  });

  it('should have reset button', () => {
    geneViewPage.resetButton.should('be.visible');
  });

  it('should have download button', () => {
    geneViewPage.downloadButton.should('be.visible');
  });

  it('should have download summary button', () => {
    geneViewPage.downloadSummaryButton.should('be.visible');
  });
});
