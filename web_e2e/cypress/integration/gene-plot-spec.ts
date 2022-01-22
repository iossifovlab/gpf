import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene plot tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  it('should have Affected status checkboxes', () => {
    geneBrowserPage.getAffectedStatusCheckbox('Affected only').should('be.visible');
    geneBrowserPage.getAffectedStatusCheckbox('Unaffected only').should('be.visible');
    geneBrowserPage.getAffectedStatusCheckbox('Affected and unaffected').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneBrowserPage.getEffectTypesCheckbox('LGDs').should('be.visible');
    geneBrowserPage.getEffectTypesCheckbox('Missense').should('be.visible');
    geneBrowserPage.getEffectTypesCheckbox('Synonymous').should('be.visible');
    geneBrowserPage.getEffectTypesCheckbox('CNV+').should('be.visible');
    geneBrowserPage.getEffectTypesCheckbox('CNV-').should('be.visible');
    geneBrowserPage.getEffectTypesCheckbox('Other').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    geneBrowserPage.getInheritanceTypes('Denovo').should('be.visible');
    geneBrowserPage.getInheritanceTypes('Transmitted').should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    geneBrowserPage.getVariantTypes('del').should('be.visible');
    geneBrowserPage.getVariantTypes('ins').should('be.visible');
    geneBrowserPage.getVariantTypes('del').should('be.visible');
    geneBrowserPage.getVariantTypes('CNV+').should('be.visible');
    geneBrowserPage.getVariantTypes('CNV-').should('be.visible');
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

  it('should have download button', () => {
    page.downloadButton.should('be.visible');
  });

  it('should have download summary button', () => {
    page.downloadSummaryButton.should('be.visible');
  });

  it('should have table legend', () => {
    cy.scrollTo('bottom');
    geneBrowserPage.legend.should('contain.text', 'affectedunaffectedmissing-person');
  });
});

describe('Gene plot summary alleles count tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
  });

  [ {checkbox: 'Affected only', expectedSummaryAllelesCount: '0 / 8'},
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

  [ {checkbox: 'LGDs', expectedSummaryAllelesCount: '1 / 8'},
    {checkbox: 'Missense', expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'Synonymous', expectedSummaryAllelesCount: '8 / 8'},
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

  [ {checkbox: 'Denovo', expectedSummaryAllelesCount: '0 / 8'},
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

  [ {checkbox: 'sub',expectedSummaryAllelesCount: '5 / 8'},
    {checkbox: 'ins',expectedSummaryAllelesCount: '7 / 8'},
    {checkbox: 'del',expectedSummaryAllelesCount: '4 / 8'},
    {checkbox: 'CNV+',expectedSummaryAllelesCount: '8 / 8'},
    {checkbox: 'CNV-',expectedSummaryAllelesCount: '8 / 8'}
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

describe('Gene plot visual tests', () => {
  const page = new GenePlotPage();
  const geneBrowserPage = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
    geneBrowserPage.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
  });

  it('should condense introns', () => {
    geneBrowserPage.searchInputBox.type('chd8');
    geneBrowserPage.goButton.click();
    page.condenseIntronsCheckbox.click();
    cy.get('g#plot').matchImageSnapshot('not-condensed-introns');

    page.condenseIntronsCheckbox.click();
    cy.get('g#plot').matchImageSnapshot('condensed-introns');
  });

  it('should compare visually TTN gene plot results', () => {
    geneBrowserPage.searchInputBox.type('ttn');
    geneBrowserPage.goButton.click();
    cy.wait(1000);
    cy.get('g#plot').matchImageSnapshot('ttn-gene-plot-snapshot');

    cy.get('gpf-table').matchImageSnapshot('ttn-gene-table-snapshot');
  });
});
