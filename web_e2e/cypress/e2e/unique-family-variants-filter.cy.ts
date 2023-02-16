
import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { UniqueFamilyVariantsFilterPage } from 'cypress/elements/unique-family-variants-filter-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Unique family variants filter tests', () => {
  const page = new UniqueFamilyVariantsFilterPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should NOT display the unique family variants filter on a single study', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.block.should('not.exist');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
    page.block.should('not.exist');
  });

  it.skip('should NOT display the unique family variants filter on a dataset with only a single study', () => {
    // ...
  });

  it('should display the unique family variants filter on a dataset with at least 2 studies inside', () => {
    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.genotypeBrowser);
    page.block.should('be.visible');

    page.navigateToDatasetPage(datasetIds.compGenotypes, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
    page.block.should('be.visible');
  });

  it.skip('should use the unique family variants filter to hide variants', () => {
    // ...
  });
});
