import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene browser tests', () => {
  const page = new GeneBrowserPage();
  const genePlotPage = new GenePlotPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should search for gene', () => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    page.searchInputBox.type('chd8');
    page.goButton.click();
    genePlotPage.window.should('be.visible');
    page.genotypePreviewTable.should('be.visible');
  });

  it('should have a Coding only checkbox', () => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    page.codingOnlyCheckbox.should('be.visible');
  });
});
