import { GenesWeights } from 'cypress/elements/genes-weights';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genes block panel tests', () => {
  const page = new GenesWeights();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });
  
  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('head to the gene weights page', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.genesWeightsPanel.should('not.exist');
  
    page.geneWeightsButton.click();
    page.genesWeightsPanel.should('be.visible');
  });

  it('should test selector buttons', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneWeightsButton.click();

    page.buttonsLowRange.should('not.exist');
    page.buttonsHighRange.should('not.exist');
    page.selectField.contains('ExAC pLI');
    page.selectField.contains('ExAC pLI rank');
    page.selectField.contains('RVIS');
    page.selectField.contains('ExAC pRec');

    page.selectField.select('ExAC pLI');

    page.buttonsLowRange.eq(0).click();

    page.inputFiledMin.should('have.value', '1e-26');
    page.inputFiledMax.should('have.value', '1.01');

    page.buttonsLowRange.eq(1).click();

    page.inputFiledMin.should('have.value', '0');
    page.inputFiledMax.should('have.value', '1.01');

    page.inputFiledMin.clear().type('1e-24').type('{enter}');
    page.inputFiledMin.should('have.value', '1e-24');
    page.gpfErrorAlert.should('not.be.visible');

    page.inputFiledMin.clear().type('3').type('{enter}');
    page.gpfErrorAlert.should('be.visible');
  });

  it('should test for changes in dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneWeightsButton.click();

    page.selectField.select('ExAC pLI');

    page.sumOfBars.should('have.text', '17993 (100.00%)');
    page.graphicsTextArray.eq(0).should('have.text', '1e-26');

    page.selectField.select('LGD score');

    page.sumOfBars.should('have.text', '18459 (100.00%)');
    page.graphicsTextArray.eq(0).should('have.text', '0');
  });

  it('should fetch table results based on the position', () => {

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.geneWeightsButton.click();

    page.selectField.select('ExAC pRec');
    page.effectPanel.contains('All').click();

    page.tablePreview.click();

    cy.get('span#variants-count-span', {timeout:10000}).should('be.visible').contains('35');

    page.effectPanel.contains('None').click();
    page.tablePreview.should('be.disabled');

    page.effectPanel.contains('Nonsense').click();
    page.tablePreview.click();
    cy.get('span#variants-count-span', {timeout:10000}).should('be.visible').contains('0');


  });
});
