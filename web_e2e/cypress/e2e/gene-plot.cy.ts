import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene plot tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
  });

  it('should have undo button', () => {
    page.undoButton.should('be.visible');
  });

  it('should have redo button', () => {
    page.redoButton.should('be.visible');
  });

  it('should have reset button', () => {
    page.resetButton.should('be.visible');
  });

  it('should have hide transcripts checkbox', () => {
    page.hideTranscriptsCheckbox.should('be.visible');
  });

  it('should have condense introns checkbox', () => {
    page.condenseIntronsCheckbox.should('be.visible');
  });

  it('should have gene title with the correct text inside', () => {
    page.geneTitle.should('have.text', 'CHD8');
  });

  it('should have summary alleles count field', () => {
    page.summaryAllelesCount.should('be.visible');
  });

  it('should have family variants count field', () => {
    page.familyVariantsCount.should('be.visible');
  });
});

describe('Gene plot summary alleles count tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
  });

  [
    {checkbox: 'Affected only', expectedSummaryAllelesCount: '0 / 8'},
    {checkbox: 'Unaffected only', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Affected and unaffected', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      geneBrowserPage.affectedStatusField.should('exist');
      page.summaryAllelesCount.should('have.text', '8 / 8');

      geneBrowserPage.getAffectedStatusCheckbox(data.checkbox).click();
      page.summaryAllelesCount.should('have.text', data.expectedSummaryAllelesCount);

      geneBrowserPage.getAffectedStatusCheckbox(data.checkbox).click();
    });
  });

  [
    {checkbox: 'LGDs', expectedSummaryAllelesCount: '1 / 8'},
    {checkbox: 'missense', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'synonymous', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV+', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Other', expectedSummaryAllelesCount: '7 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      geneBrowserPage.effectTypeFiltersField.should('exist');
      page.summaryAllelesCount.should('have.text', '8 / 8');

      geneBrowserPage.getEffectTypesCheckbox(data.checkbox).click();
      page.summaryAllelesCount.should('have.text', data.expectedSummaryAllelesCount);

      geneBrowserPage.getEffectTypesCheckbox(data.checkbox).click()
    });
  });

  [
    {checkbox: 'Denovo', expectedSummaryAllelesCount: '0 / 8'},
    {checkbox: 'Transmitted', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      geneBrowserPage.inheritanceTypesFilter.should('exist');
      page.summaryAllelesCount.should('have.text', '8 / 8');

      geneBrowserPage.getInheritanceTypes(data.checkbox).click();
      page.summaryAllelesCount.should('have.text', data.expectedSummaryAllelesCount);

      geneBrowserPage.getInheritanceTypes(data.checkbox).click();
    });
  });

  [
    {checkbox: 'sub', expectedSummaryAllelesCount: '5 / 8'},
    {checkbox: 'ins', expectedSummaryAllelesCount: '7 / 8'},
    {checkbox: 'del', expectedSummaryAllelesCount: '4 / 8'},
    {checkbox: 'CNV+', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedSummaryAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      geneBrowserPage.variantTypesFilter.should('exist');
      page.summaryAllelesCount.should('have.text', '8 / 8');

      geneBrowserPage.getVariantTypes(data.checkbox).click();
      page.summaryAllelesCount.should('have.text', data.expectedSummaryAllelesCount);

      geneBrowserPage.getVariantTypes(data.checkbox).click();
    });
  });
});

describe.skip('Gene plot visual tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
  });

  it('should condense introns', () => {
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.pressGoButton();
    page.condenseIntronsCheckbox.click();
    cy.get('g#plot').matchImageSnapshot('not-condensed-introns');

    page.condenseIntronsCheckbox.click();
    cy.get('g#plot').matchImageSnapshot('condensed-introns');
  });

  it('should compare visually TTN gene plot results', () => {
    geneBrowserPage.searchInputBox.type('ttn');
    geneBrowserPage.pressGoButton();
    cy.get('g#plot').matchImageSnapshot('ttn-gene-plot-snapshot');

    page.variantsCount.should('exist');
    page.variantsCount.should('have.text', '19 variants selected');
    cy.get('gpf-table').matchImageSnapshot('ttn-gene-table-snapshot');
  });
});
