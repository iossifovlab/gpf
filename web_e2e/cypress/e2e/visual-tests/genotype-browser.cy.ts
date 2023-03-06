import { GenesBlockPage } from 'cypress/elements/genes-block-page';
import { GenotypeBrowserController } from 'cypress/elements/genotype-browser-controller';
import { GenotypeBrowserPage } from 'cypress/elements/genotype-browser-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genotype browser visual tests', () => {
  const genotypeBrowserPage = new GenotypeBrowserPage();
  const genotypeBrowserController = new GenotypeBrowserController();

  before(() => {
    genotypeBrowserPage.cleanup();
    genotypeBrowserPage.navigateToHome(false);
    genotypeBrowserPage.loginAdmin();
  });

  beforeEach(() => {
    genotypeBrowserPage.preserveLogin();
    genotypeBrowserPage.navigateToHome();
    genotypeBrowserPage.prepareForVisualTest();
  });

  [
    'CHD8', 'POGZ', 'KDM5B', 'TTLL10'
  ].forEach(geneSymbol => {
    it('should compare ' + geneSymbol + ' gene results', () => {
      const genesBlockPage = new GenesBlockPage();
      genotypeBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.genotypeBrowser);

      genesBlockPage.geneSymbolsButton.click();
      genesBlockPage.geneSymbolsTextarea.clear().type(geneSymbol);

      genotypeBrowserController.pressTablePreviewButton();
      cy.matchImage();
    });
  });
});