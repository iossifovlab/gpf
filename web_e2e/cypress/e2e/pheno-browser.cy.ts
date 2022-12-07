import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno browser tests', () => {
  const page = new PhenoBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  [
    {seachQuery: 'the age'},
    {seachQuery: 'the iq'},
    {seachQuery: 'measure 1'},
    {seachQuery: 'measure 2'},
    {seachQuery: 'measure 3'},
    {seachQuery: 'measure 4'}
  ].forEach(data => {
    it('should filter the right rows when typing "' + data.seachQuery + '" in the sarchbox', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

      page.allTableRows.should('have.length', 8);

      page.searchInputBox.type(data.seachQuery);
      page.allTableRows.should('have.length', 1);
    });
  });

  it('should filter the right rows when typing "1" in the sarchbox', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

    page.allTableRows.should('have.length', 8);

    page.searchInputBox.type('1');
    page.allTableRows.should('have.length', 7);
  });

  it('should filter the right rows using the instruments dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

    page.allTableRows.should('have.length', 8);

    page.instrumentsBox.select('i1');
    page.allTableRows.should('have.length', 7);

    page.instrumentsBox.select('pheno_common');
    page.allTableRows.should('have.length', 1);

    page.instrumentsBox.select('All instruments');
    page.allTableRows.should('have.length', 8);
  });

  it('should have working table header sorting buttons', { scrollBehavior: false }, () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

    page.tableCells.eq(0).should('have.text', 'i1');

    page.headerCells.eq(0).click();
    page.tableCells.eq(0).should('have.text', 'pheno_common');

    page.headerCells.eq(0).click();
    page.tableCells.eq(0).should('have.text', 'i1');

    page.headerCells.eq(1).click();
    page.tableCells.eq(1).should('have.text', 'sample_id');

    page.headerCells.eq(1).click();
    page.tableRows.eq(1).get('gpf-table-view-cell').eq(1).should('have.text', 'age');

    page.headerCells.eq(1).click();
    page.tableRows.eq(1).get('gpf-table-view-cell').eq(1).should('have.text', 'sample_id');

    page.headerCells.eq(2).click();
    page.tableRows.eq(2).get('gpf-table-view-cell').eq(2).should('have.text', 'The IQ of the individual');

    page.headerCells.eq(2).click();
    page.tableRows.eq(2).get('gpf-table-view-cell').eq(2).should('have.text', '');
  });

  it.only('should have the correct text values in all rows', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

    const expectedFilePath = 'cypress/fixtures/pheno-browser/row_values.txt';
    cy.readFile(expectedFilePath, { timeout: 5000 }).then((expectedFile: string) => {
      const rowValues = expectedFile.split(',\n');

      for (let i = 0; i < rowValues.length; i++) {
        page.tableRows.eq(i).should('have.text', rowValues[i]);
      }
    });
  });

  it('should download all instruments and validate whether they are equal to the reference data', () => {
    const downloadFilePath = Cypress.config('downloadsFolder') + '/measures_comp_all.csv';
    const expectedFilePath = 'cypress/fixtures/pheno-browser/measures_comp_all.csv';

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    page.instrumentsBox.select('All instruments');

    page.downloadInstrumentsButton.click();
    cy.readFile(downloadFilePath, { timeout: 5000 }).then((downloadedFile: string) => {
      cy.readFile(expectedFilePath, { timeout: 5000 }).then((expectedFile: string) => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });
  });
});
