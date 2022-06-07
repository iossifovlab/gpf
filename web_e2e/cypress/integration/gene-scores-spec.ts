import { GeneScoresPage } from 'cypress/elements/gene-scores-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

const geneScoresData = [
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
  const page = new GeneScoresPage();
  const genesBlockPage = new GenesBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display gene weights panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.genesWeightsPanel.should('not.exist');

    genesBlockPage.geneScoresButton.click();
    genesBlockPage.genesWeightsPanel.should('be.visible');
  });

  it('should display the correct gene weights in the selector dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();

    geneScoresData.forEach(geneScore => {
      page.dropdownButton.contains(geneScore.desc);
    });
  });

  it('should go through all gene weights and check whether from/to buttons are shown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();

    geneScoresData.forEach(geneScore => {
      page.dropdownButton.select(geneScore.desc);
      page.fromInputField.should(geneScore.inputField ? 'be.visible' : 'not.exist');
      page.toInputField.should(geneScore.inputField ? 'be.visible' : 'not.exist');
    });
  });

  it('should have working from/to step up/down buttons in RVIS rank', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();
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
    genesBlockPage.geneScoresButton.click();
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

  geneScoresData.forEach(geneScore => {
    it('should filter variants when "' + geneScore.desc + '" gene score is selected', () => {
      const genotypeBrowserController = new GenotypeBrowserController();
      const genotypeBrowserPage = new GenotypeBrowserPage();

      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
      genesBlockPage.geneScoresButton.click();
      page.dropdownButton.select(geneScore.desc);
      page.allGeneScores.should('not.contain', '~');

      genotypeBrowserController.setEffectTypesGroup('All');
      genotypeBrowserController.pressTablePreviewButton();
      genotypeBrowserPage.overviewParagraph.should(
        'have.text',
        geneScore.allVariants + ' variants selected (' + geneScore.allVariants + ' shown)'
      );
    });
  });
});

describe.skip('Gene weights visual tests', () => {
  const page = new GeneScoresPage();
  const genesBlockPage = new GenesBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it.skip('should inspect gene weights on drag', () => {
    function moveSlider(which: string, dragValue, heightValue = 0): void {
      if (which === 'right') {
        dragValue = -dragValue;
      }
      cy.window().then(win => {
        cy.get('g[gpf-histogram-range-selector-line] > g > line').eq(which === 'left' ? 0 : 1)
          .trigger("mousedown", 0, heightValue, { // start value, height value
            view: win,
            which: 1,
            force: true,
            bubbles: true
          })
          .trigger("mousemove", dragValue, heightValue, { // how much to be dragged value, height value
            which: 1,
            force: true,
            bubbles: true
          })
          .trigger("mouseup", 0, heightValue, { // end value, height value
            which: 1,
            force: true,
            view: win,
            bubbles: true
          });
      });
    }

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();

    moveSlider('left', 200);
    page.allGeneScores.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-drag-200');

    moveSlider('left', -100);
    page.allGeneScores.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-drag-100');

    moveSlider('left', -100);
    moveSlider('right', 100);
    page.allGeneScores.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-right-drag-100');

    moveSlider('left', 200);
    page.allGeneScores.should('not.contain.text', '~');
    page.histogram.matchImageSnapshot('histogram-left-right-drag-overlap');
  });
});
