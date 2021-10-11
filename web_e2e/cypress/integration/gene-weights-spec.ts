import { GenesWeights } from 'cypress/elements/genes-weights';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

describe('Gene weights panel tests', () => {
  const page = new GenesWeights();
  const genesBlockPage = new GenesBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });
  
  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display gene weights panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.genesWeightsPanel.should('not.exist');
  
    genesBlockPage.geneWeightsButton.click();
    genesBlockPage.genesWeightsPanel.should('be.visible');
  });

  it('should display the correct gene weights in the selector dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();

    page.dropdownButton.contains('SFARI gene score');
    page.dropdownButton.contains('RVIS rank');
    page.dropdownButton.contains('RVIS');
    page.dropdownButton.contains('LGD rank');
    page.dropdownButton.contains('LGD score');
    page.dropdownButton.contains('ExAC pLI rank');
    page.dropdownButton.contains('ExAC pLI');
    page.dropdownButton.contains('ExAC pRec rank');
    page.dropdownButton.contains('ExAC pRec');
  });

  it('should go through all gene weights and check whether from/to buttons are shown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();

    page.dropdownButton.should('contain', 'SFARI gene score');
    page.fromInputField.should('not.exist');
    page.toInputField.should('not.exist');

    page.dropdownButton.select('RVIS rank');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('RVIS');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('LGD rank');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('LGD score');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('ExAC pLI rank');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('ExAC pLI');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('ExAC pRec rank');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');

    page.dropdownButton.select('ExAC pRec');
    page.fromInputField.should('be.visible');
    page.toInputField.should('be.visible');
  });

  it('should have working from/to step up/down buttons in RVIS rank', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();
    page.dropdownButton.select('RVIS rank');

    page.fromInputField.should('have.value', '1');
    page.toInputField.should('have.value', '16754');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '112.687');
    page.toInputField.should('have.value', '16642.313');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '1');
    page.toInputField.should('have.value', '16754');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '1');
    page.toInputField.should('have.value', '16754');
  });

  it('should have working from/to step up/down buttons in ExAC pLI', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();
    page.dropdownButton.select('ExAC pLI');

    page.fromInputField.should('have.value', '0');
    page.toInputField.should('have.value', '1.01');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '1e-26');
    page.toInputField.should('have.value', '0.676');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '1.49e-26');
    page.toInputField.should('have.value', '0.452');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '1e-26');
    page.toInputField.should('have.value', '0.676');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '0');
    page.toInputField.should('have.value', '1.01');
  });

  it('should filter variants based on selected gene weight', () => {
    const genotypeBrowserController = new GenotypeBrowserController();
    const genotypeBrowserPage = new GenotypeBrowserPage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBrowserController.setEffectTypesToAll();
    genesBlockPage.geneWeightsButton.click();

    page.dropdownButton.select('SFARI gene score');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '0 variants selected (0 shown)');

    page.dropdownButton.select('RVIS rank');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '0 variants selected (0 shown)');

    page.dropdownButton.select('RVIS');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '0 variants selected (0 shown)');

    page.dropdownButton.select('LGD rank');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');
    
    page.dropdownButton.select('LGD score');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');

    page.dropdownButton.select('ExAC pRec');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');

    page.dropdownButton.select('ExAC pLI rank');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');

    page.dropdownButton.select('ExAC pLI');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');
    
    page.dropdownButton.select('ExAC pRec rank');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');

    page.dropdownButton.select('ExAC pRec');
    cy.wait(1000);
    genotypeBrowserController.showTablePreview();
    genotypeBrowserPage.overviewParagraph.should('have.text', '35 variants selected (35 shown)');
  });
});
