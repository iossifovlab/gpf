import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GeneViewPage } from 'cypress/elements/gene-view-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Gene view tests', () => {
  const geneViewPage = new GeneViewPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    geneViewPage.cleanup();
    geneViewPage.navigateToHome();
    geneViewPage.loginAdmin();
  });

  beforeEach(() => {
    geneViewPage.preserveLogin();
    geneViewPage.navigateToHome();

    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  it('should have Affected status checkboxes', () => {
    geneViewPage.affectedStatusAffectedOnlyCheckbox.should('be.visible');
    geneViewPage.affectedStatusUnaffectedOnlyCheckbox.should('be.visible');
    geneViewPage.affectedStatusAffectedAndUnaffectedCheckbox.should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneViewPage.effectTypesLGDsCheckbox.should('be.visible');
    geneViewPage.effectTypesMissenseCheckbox.should('be.visible');
    geneViewPage.effectTypesSynonymousCheckbox.should('be.visible');
    geneViewPage.effectTypesCNVPlusCheckbox.should('be.visible');
    geneViewPage.effectTypesCNVMinusCheckbox.should('be.visible');
    geneViewPage.effectTypesOtherCheckbox.should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneViewPage.inheritanceTypesDenovoCheckbox.should('be.visible');
    geneViewPage.inheritanceTypesTransmittedCheckbox.should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    geneViewPage.variantTypesSubCheckbox.should('be.visible');
    geneViewPage.variantTypesInsCheckbox.should('be.visible');
    geneViewPage.variantTypesDelCheckbox.should('be.visible');
    geneViewPage.variantTypesCNVPlusCheckbox.should('be.visible');
    geneViewPage.variantTypesCNVMinusCheckbox.should('be.visible');
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
