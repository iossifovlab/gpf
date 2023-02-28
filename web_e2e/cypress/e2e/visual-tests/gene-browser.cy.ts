import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene browser visual tests', () => {
  const geneBrowserPage = new GeneBrowserPage();
  const genePlotPage = new GenePlotPage();

  before(() => {
    geneBrowserPage.cleanup();
    geneBrowserPage.navigateToHome(false);
    geneBrowserPage.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
  });

  it('should condense introns', () => {
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
    genePlotPage.condenseIntronsCheckbox.click();
    cy.get('g#plot').scrollTo('center', {ensureScrollable: false}).then(() => {
      cy.get('g#plot').matchImageSnapshot('not-condensed-introns');
    });

    genePlotPage.condenseIntronsCheckbox.click();
    cy.get('g#plot').scrollTo('center', {ensureScrollable: false}).then(() => {
      cy.get('g#plot').matchImageSnapshot('condensed-introns');
    });
  });

  it('should compare visually TTN gene plot results', () => {
    geneBrowserPage.searchInputBox.type('ttn');
    geneBrowserPage.pressGoButton();
    cy.get('gpf-genotype-preview-table').scrollTo('center', {ensureScrollable: false}).then(() => {
      cy.matchImageSnapshot('ttn-gene-plot-snapshot');
    });
  });
});