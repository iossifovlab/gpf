import { GeneWeightsPage } from 'cypress/elements/gene-weights-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

const geneWeightsData = [
  {
    desc: "SFARI gene score",
    inputField: false,
    allVariants: '0'
  },
  {
    desc: "RVIS rank",
    inputField: true,
    allVariants: '0'
  },
  {
    desc: "RVIS",
    inputField: true,
    allVariants: '0'
  },
  {
    desc: "LGD rank",
    inputField: true,
    allVariants: '35'
  },
  {
    desc: "LGD score",
    inputField: true,
    allVariants: '35'
  },
  {
    desc: "ExAC pLI rank",
    inputField: true,
    allVariants: '35'
  },
  {
    desc: "ExAC pLI",
    inputField: true,
    allVariants: '35'
  },
  {
    desc: "ExAC pRec rank",
    inputField: true,
    allVariants: '35'
  },
  {
    desc: "ExAC pRec",
    inputField: true,
    allVariants: '35'
  }
];

describe('Gene weights panel tests', () => {
  const page = new GeneWeightsPage();
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

    geneWeightsData.forEach(geneWeight => {
      page.dropdownButton.contains(geneWeight.desc);
    });
  });

  it('should go through all gene weights and check whether from/to buttons are shown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();

    geneWeightsData.forEach(geneWeight => {
      page.dropdownButton.select(geneWeight.desc);
      page.fromInputField.should(geneWeight.inputField ? 'be.visible' : 'not.exist');
      page.toInputField.should(geneWeight.inputField ? 'be.visible' : 'not.exist');
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

  geneWeightsData.forEach(geneWeight => {
    it('should filter variants when "' + geneWeight.desc + '" gene weight is selected', () => {
      const genotypeBrowserController = new GenotypeBrowserController();
      const genotypeBrowserPage = new GenotypeBrowserPage();

      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
      genotypeBrowserController.setEffectTypesToAll();
      genesBlockPage.geneWeightsButton.click();

      page.dropdownButton.select(geneWeight.desc);
      page.allGeneWeights.should('not.contain', '~');
  
      genotypeBrowserController.showTablePreview();
      genotypeBrowserPage.overviewParagraph.should('have.text', geneWeight.allVariants + ' variants selected (' + geneWeight.allVariants + ' shown)');
    });
  });
});

describe.skip('Gene weights visual tests', () => {
  const page = new GeneWeightsPage();
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

  it('should inspect gene weights on drag', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneWeightsButton.click();

    page.moveSlider('left', 200);
    page.allGeneWeights.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-drag-200');
    page.moveSlider('left', -100);
    page.allGeneWeights.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-drag-100');
    page.moveSlider('left', -100);
    page.moveSlider('right', 100);
    page.allGeneWeights.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-right-drag-100');
    page.moveSlider('left', 200);
    page.allGeneWeights.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-right-drag-overlap');
  });
});
