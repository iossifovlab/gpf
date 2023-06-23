import { GeneScoresPage } from 'cypress/elements/gene-scores-page';
import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';

const geneScoresData = [
  {
    desc: 'SFARI gene score',
    inputField: false,
    allVariants: '30'
  },
  {
    desc: 'RVIS rank',
    inputField: true,
    allVariants: '0'
  },
  {
    desc: 'RVIS',
    inputField: true,
    allVariants: '0'
  },
  {
    desc: 'LGD rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'LGD score',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pLI rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pLI',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pRec rank',
    inputField: true,
    allVariants: '30'
  },
  {
    desc: 'ExAC pRec',
    inputField: true,
    allVariants: '30'
  }
];

describe('Gene scores tests', () => {
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

  it('should display gene scores panel', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresPanel.should('not.exist');

    genesBlockPage.geneScoresButton.click();
    genesBlockPage.geneScoresPanel.should('be.visible');
  });

  it('should show all the gene scores in the selector dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();

    geneScoresData.forEach(geneScore => {
      page.dropdownButton.contains(geneScore.desc);
    });
  });

  it('should go through all gene scores and check whether the from/to buttons are shown or hidden', () => {
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
    page.toInputField.should('have.value', '16640');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '111.927');
    page.toInputField.should('have.value', '16529.073');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '1');
    page.toInputField.should('have.value', '16640');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '1');
    page.toInputField.should('have.value', '16640');
  });

  it('should have working from/to step up/down buttons in ExAC pLI', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();
    page.dropdownButton.select('ExAC pLI');

    page.fromInputField.should('have.value', '0');
    page.toInputField.should('have.value', '1');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '0.00001');
    page.toInputField.should('have.value', '0.912');

    page.fromFieldStepUp.click();
    page.toFieldStepDown.click();
    page.fromInputField.should('have.value', '0.000011');
    page.toInputField.should('have.value', '0.832');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '0.00001');
    page.toInputField.should('have.value', '0.912');

    page.toFieldStepUp.click();
    page.fromFieldStepDown.click();
    page.fromInputField.should('have.value', '0');
    page.toInputField.should('have.value', '1');
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
        geneScore.allVariants + ' variants selected'
      );
    });
  });
});

describe('Gene scores download tests', () => {
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
    cy.deleteDownloadsFolder();
  });

  it('should download RVIS and compare the file to the reference data', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genesBlockPage.geneScoresButton.click();
    page.dropdownButton.select('RVIS');

    const downloadedVariantsPath = Cypress.config('downloadsFolder') + '/scores.csv';
    const expectedVariantsPath = 'cypress/fixtures/gene-scores/scores.csv';

    cy.window().document().then(doc => {
      doc.addEventListener('click', () => {
        setTimeout(() => doc.location?.reload(), 20000);
      });
      page.downloadLink.click();
    });

    cy.readFile(downloadedVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
      cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });
  });
});
