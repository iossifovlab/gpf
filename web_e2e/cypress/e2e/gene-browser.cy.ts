import { GeneBrowserPage } from 'cypress/elements/gene-browser-page';
import { GenePlotPage } from 'cypress/elements/gene-plot-page';
import { GenotypePreviewTablePage } from 'cypress/elements/genotype-preview-table-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Gene browser basic display tests before query', () => {
  const page = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
  });

  it('should display "Gene Symbol" card title', () => {
    page.geneSymbolHeader.should('be.visible');
  });

  it('should display search box', () => {
    page.searchInputBox.should('be.visible');
  });

  it('should display the "Coding only" checkbox', () => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    page.codingOnlyCheckbox.should('be.visible');
  });

  it('should display the "Go" button', () => {
    page.goButton.should('be.visible');
  });

  it('should NOT display the filters', () => {
    page.filters.should('not.exist');
  });

  it('should NOT display the gene plot', () => {
    const genePlotPage = new GenePlotPage();
    genePlotPage.window.should('not.exist');
  });

  it('should NOT display the genotype preview table', () => {
    const genotypePreviewTablePage = new GenotypePreviewTablePage();
    genotypePreviewTablePage.table.should('not.exist');
  });
});

describe('Gene browser basic display tests after query', () => {
  const page = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    page.searchInputBox.type('chd8');
    page.pressGoButton();
  });

  it('should display the filters', () => {
    page.filters.should('be.visible');
  });

  it('should display the gene plot', () => {
    const genePlotPage = new GenePlotPage();
    genePlotPage.window.should('be.visible');
  });

  it('should display the genotype preview table', () => {
    const genotypePreviewTablePage = new GenotypePreviewTablePage();
    genotypePreviewTablePage.table.should('be.visible');
  });

  it('should have Affected status checkboxes', () => {
    page.getAffectedStatusCheckbox('Affected only').should('be.visible');
    page.getAffectedStatusCheckbox('Unaffected only').should('be.visible');
    page.getAffectedStatusCheckbox('Affected and unaffected').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getEffectTypesCheckbox('LGDs').should('be.visible');
    page.getEffectTypesCheckbox('missense').should('be.visible');
    page.getEffectTypesCheckbox('synonymous').should('be.visible');
    page.getEffectTypesCheckbox('CNV+').should('be.visible');
    page.getEffectTypesCheckbox('CNV-').should('be.visible');
    page.getEffectTypesCheckbox('Other').should('be.visible');
  });

  it('should have effect types checkboxes', () => {
    page.getInheritanceTypes('Denovo').should('be.visible');
    page.getInheritanceTypes('Transmitted').should('be.visible');
  });

  it('should have variant types checkboxes', () => {
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('ins').should('be.visible');
    page.getVariantTypes('del').should('be.visible');
    page.getVariantTypes('CNV+').should('be.visible');
    page.getVariantTypes('CNV-').should('be.visible');
  });

  it('should have download summary button', () => {
    page.downloadSummaryButton.should('be.visible');
  });

  it('should have download button', () => {
    page.downloadButton.should('be.visible');
  });
});

describe('Gene browser download tests', () => {
  const page = new GeneBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    cy.deleteDownloadsFolder();
  });

  [
    {
      gene: 'chd8',
      filtersToUncheck: ['Other', 'ins'],
      expectedPaths: [
        'summary_variants1.tsv',
        'variants1.tsv'
      ]
    },
    {
      gene: 'chd8',
      filtersToUncheck: ['Affected only'],
      expectedPaths: [
        'summary_variants2.tsv',
        'variants2.tsv'
      ]
    },
    {
      gene: 'pogz',
      filtersToUncheck: ['missense', 'synonymous'],
      expectedPaths: [
        'summary_variants3.tsv',
        'variants3.tsv'
      ]
    }
  ].forEach(data => {
    it('should go to ' + data.gene + ' gene page, filter out ' + data.filtersToUncheck.toString() +
       'download summary and family variants and compare the files to the reference data', () => {
      page.searchInputBox.type(data.gene);
      page.pressGoButton();

      data.filtersToUncheck.forEach(filter => {
        page.getAffectedStatusCheckbox(filter).click();
      });

      page.downloadSummaryButton.click();
      page.downloadButton.click();

      const paths = ['/summary_variants.tsv', '/variants.tsv'];
      paths.forEach((path, i) => {
        const downloadedSummaryVariantsPath = Cypress.config('downloadsFolder') + path;
        const expectedVariantsPath = 'cypress/fixtures/gene-browser/' + data.expectedPaths[i];

        cy.readFile(downloadedSummaryVariantsPath, { timeout: 10000 }).then((downloadedFile: string) => {
          cy.readFile(expectedVariantsPath, { timeout: 10000 }).then((expectedFile: string) => {
            const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
            const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
            expect(downloadedFileLines).to.deep.eq(expectedFileLines);
          });
        });
      });
    });
  });
});
