import { GenesWeights } from 'cypress/elements/genes-weights';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

const geneWeightsData = [
  {
    name: "SFARI_gene_score",
    desc: "SFARI gene score",
    inputField: false,
    values: [

    ], allVariants: '0'
  },
  {
    name: "RVIS_rank",
    desc: "RVIS rank",
    inputField: true,
    values: [

    ], allVariants: '0'
  },
  {
    name: "RVIS",
    desc: "RVIS",
    inputField: true,
    values: [
      
    ], allVariants: '0'
  },
  {
    name: "LGD_rank",
    desc: "LGD rank",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  },
  {
    name: "LGD_score",
    desc: "LGD score",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  },
  {
    name: "pLI_rank",
    desc: "ExAC pLI rank",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  },
  {
    name: "pLI",
    desc: "ExAC pLI",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  },
  {
    name: "pRec_rank",
    desc: "ExAC pRec rank",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  },
  {
    name: "pRec",
    desc: "ExAC pRec",
    inputField: true,
    values: [
      
    ], allVariants: '35'
  }
];

/*
function wait_for_query(name = 'query', type = 'POST', url: string, response?: number, times = 1) {
  if(!(times > 0))
    return;
  while(times-- > 0) {
    cy.intercept(type, url).as(name);
    cy.wait('@' + name).its('response.statusCode').should('eq', response ? response : 200);
  }
}
*/

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

    geneWeightsData.forEach(element => {
      page.dropdownButton.contains(element.desc);
    });
  });

  it('should go through all gene weights and check whether from/to buttons are shown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();

    geneWeightsData.forEach(element => {
      page.dropdownButton.select(element.desc);
      console.log(element.inputField);
      page.fromInputField.should(element.inputField ? 'be.visible' : 'not.exist');
      page.toInputField.should(element.inputField ? 'be.visible' : 'not.exist');
    });
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

    geneWeightsData.forEach(element => {
      page.dropdownButton.select(element.desc);
      //wait_for_query('reponse', 'POST', '/gpf/api/v3/gene_weights/partitions', 200, 3);
      page.allGeneWeights.should('not.contain', '~');
  
      genotypeBrowserController.showTablePreview();
      genotypeBrowserPage.overviewParagraph.should('have.text', element.allVariants + ' variants selected (' + element.allVariants + ' shown)');
    });

  });
});
