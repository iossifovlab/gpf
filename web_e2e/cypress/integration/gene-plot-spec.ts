import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene plot tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  it('should have Affected status checkboxes', () => {
    page.getAffectedStatusCheckbox('Affected only').should('be.visible');
    page.getAffectedStatusCheckbox('Unaffected only').should('be.visible');
    page.getAffectedStatusCheckbox('Affected and unaffected').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getEffectTypesCheckbox('LGDs').should('be.visible');
    page.getEffectTypesCheckbox('Missense').should('be.visible');
    page.getEffectTypesCheckbox('Synonymous').should('be.visible');
    page.getEffectTypesCheckbox('CNV+').should('be.visible');
    page.getEffectTypesCheckbox('CNV-').should('be.visible');
    page.getEffectTypesCheckbox('Other').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getInheritanceTypes('Denovo').should('be.visible');
    page.getInheritanceTypes('Transmitted').should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('ins').should('be.visible');
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('CNV+').should('be.visible');
    page.getVariantTypes('CNV-').should('be.visible');
  });

  it('should have undo button', () => {
    page.undoButton.should('be.visible');
  });

  it('should have redo button', () => {
    page.redoButton.should('be.visible');
  });

  it('should have reset button', () => {
    page.resetButton.should('be.visible');
  });

  it('should have download button', () => {
    page.downloadButton.should('be.visible');
  });

  it('should have download summary button', () => {
    page.downloadSummaryButton.should('be.visible');
  });
});
