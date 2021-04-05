import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Gene browser tests', () => {
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    geneBrowserPage.navigateToHome();
    geneBrowserPage.loginAdmin();
  });

  after(() => {
    geneBrowserPage.logout();
  });

  beforeEach(() => {
    geneBrowserPage.navigateToHome();
  });

  it('should search for gene', () => {
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
    geneBrowserPage.geneView.should('be.visible');
    geneBrowserPage.genotypePreviewTable.should('be.visible');
  });

  it('should have a Coding only checkbox', () => {
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageNames.geneBrowser);
    geneBrowserPage.codingOnlyCheckbox.should('be.visible');
  });
});
