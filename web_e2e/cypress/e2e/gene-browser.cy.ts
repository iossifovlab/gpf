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

  it('should have family variants count', () => {
    page.familyAllelesCount.should('be.visible');
  });

  it('should have download family varinats button', () => {
    page.downloadFamilyVariantsButton.should('be.visible');
  });
});

describe('Gene browser family alleles count and table tests', () => {
  const page = new GeneBrowserPage();
  const genotypePreviewTablePage = new GenotypePreviewTablePage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    page.navigateToDatasetPage(datasetIds.iossifov2014, toolPageLinks.geneBrowser);
    page.searchInputBox.type('chd8');
    page.pressGoButton();
  });

  [
    {checkbox: 'Affected only', expectedFamilyAllelesCount: '0 / 8'},
    {checkbox: 'Unaffected only', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'Affected and unaffected', expectedFamilyAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      page.affectedStatusField.should('exist');
      page.familyAllelesCount.should('have.text', '8 / 8');

      page.getAffectedStatusCheckbox(data.checkbox).click();
      page.familyAllelesCount.should('have.text', data.expectedFamilyAllelesCount);

      page.getAffectedStatusCheckbox(data.checkbox).click();
    });
  });

  [
    {checkbox: 'LGDs', expectedFamilyAllelesCount: '1 / 8'},
    {checkbox: 'missense', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'synonymous', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'CNV+', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'Other', expectedFamilyAllelesCount: '7 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      page.effectTypeFiltersField.should('exist');
      page.familyAllelesCount.should('have.text', '8 / 8');

      page.getEffectTypesCheckbox(data.checkbox).click();
      page.familyAllelesCount.should('have.text', data.expectedFamilyAllelesCount);

      page.getEffectTypesCheckbox(data.checkbox).click();
    });
  });

  [
    {checkbox: 'Denovo', expectedFamilyAllelesCount: '0 / 8'},
    {checkbox: 'Transmitted', expectedFamilyAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      page.inheritanceTypesFilter.should('exist');
      page.familyAllelesCount.should('have.text', '8 / 8');

      page.getInheritanceTypes(data.checkbox).click();
      page.familyAllelesCount.should('have.text', data.expectedFamilyAllelesCount);

      page.getInheritanceTypes(data.checkbox).click();
    });
  });

  [
    {checkbox: 'sub', expectedFamilyAllelesCount: '5 / 8'},
    {checkbox: 'ins', expectedFamilyAllelesCount: '7 / 8'},
    {checkbox: 'del', expectedFamilyAllelesCount: '4 / 8'},
    {checkbox: 'CNV+', expectedFamilyAllelesCount: '8 / 8'},
    {checkbox: 'CNV-', expectedFamilyAllelesCount: '8 / 8'}
  ].forEach(data => {
    it('should display the correct value when filtering with the "' + data.checkbox + '" checkbox', () => {
      page.variantTypesFilter.should('exist');
      page.familyAllelesCount.should('have.text', '8 / 8');

      page.getVariantTypes(data.checkbox).click();
      page.familyAllelesCount.should('have.text', data.expectedFamilyAllelesCount);

      page.getVariantTypes(data.checkbox).click();
    });
  });

  it('should check table rows count', () => {
    genotypePreviewTablePage.selectedVariants.then((selectedVarinats) => {
      const text = selectedVarinats.text();
      const regex = new RegExp(/^[^\d]*(\d+)/);
      const numberOfRows = Number(text.match(regex)[0]);
      page.familyAllelesCount.should('not.contain', '0 /');
      genotypePreviewTablePage.getRows.should('have.length', numberOfRows);
    });
  });

  it('should check table if nothing found is shown with filter Denovo', () => {
    page.getInheritanceTypes('Denovo').click();
    genotypePreviewTablePage.getNothingFound.should('be.visible');
    genotypePreviewTablePage.selectedVariants.then((selectedVarinats) => {
      const text = selectedVarinats.text();
      const regex = new RegExp(/^[^\d]*(\d+)/);
      const numberOfRows = Number(text.match(regex)[0]);
      genotypePreviewTablePage.getRows.should('have.length', 0);
      page.familyAllelesCount.contains('0 /');
      expect(numberOfRows).to.eq(0);
    });

    page.getInheritanceTypes('Denovo').click();
    genotypePreviewTablePage.getNothingFound.should('not.exist');
  });

  it('should check table rows when sub, ins and CNV+ are unchecked', () => {
    page.getVariantTypes('sub').click();
    page.getVariantTypes('ins').click();
    page.getVariantTypes('CNV+').click();

    genotypePreviewTablePage.selectedVariants.then((selectedVarinats) => {
      const text = selectedVarinats.text();
      const regex = new RegExp(/^[^\d]*(\d+)/);
      const numberOfRows = Number(text.match(regex)[0]);
      genotypePreviewTablePage.getRows.should('have.length', numberOfRows);
      page.familyAllelesCount.should('not.contain', '0 /');
    });
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

  it('should go to chd8 gene page, filter out Affected only ' +
    'family variants and check if download button is disabled', () => {
    page.searchInputBox.type('chd8');
    page.pressGoButton();
    page.getAffectedStatusCheckbox('Affected only').click();
    page.downloadFamilyVariantsButton.should('be.disabled');
  });

  [
    {
      gene: 'chd8',
      filtersToUncheck: ['Other', 'ins'],
      expectedPath: 'variants1.tsv'
    },
    {
      gene: 'pogz',
      filtersToUncheck: ['missense', 'synonymous'],
      expectedPath: 'variants2.tsv'
    }
  ].forEach(data => {
    it('should go to ' + data.gene + ' gene page, filter out ' + data.filtersToUncheck.toString() +
      'family variants and compare the files to the reference data', () => {
      page.searchInputBox.type(data.gene);
      page.pressGoButton();

      data.filtersToUncheck.forEach(filter => {
        page.getAffectedStatusCheckbox(filter).click();
      });

      cy.window().document().then(doc => {
        doc.addEventListener('click', () => {
          setTimeout(() => doc.location?.reload(), 20000);
        });
        page.downloadFamilyVariantsButton.click();
      });

      const downloadedFamilyVariantsPath = Cypress.config('downloadsFolder') + '/variants.tsv';
      const expectedVariantsPath = 'cypress/fixtures/gene-browser/' + data.expectedPath;

      cy.readFile(downloadedFamilyVariantsPath, { timeout: 20000 }).then((downloadedFile: string) => {
        cy.readFile(expectedVariantsPath, { timeout: 20000 }).then((expectedFile: string) => {
          const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
          const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
          expect(downloadedFileLines).to.deep.eq(expectedFileLines);
        });
      });
    });
  });
});
