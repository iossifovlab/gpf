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

    cy.intercept('POST', '/gpf/api/v3/gene_weights/partitions*', (req) => {
      expect(req.body).to.deep.equal({
        "weight": "pLI",
        "min": 1e-26,
        "max": 1.01
      });
    }).as('getInputValueUp');

    cy.wait('@getInputValueUp');

    page.buttonsLowRange.eq(1).click();

    cy.intercept('POST', '/gpf/api/v3/gene_weights/partitions*', (req) => {
      expect(req.body).to.deep.equal({
        "weight": "pLI",
        "min": 0,
        "max": 1.01
      });
    });
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
});
