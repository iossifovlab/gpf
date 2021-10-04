import { should } from 'chai';
import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Pheno browser tests', () => {
  const page = new PhenoBrowserPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  [{seachQuery: 'the age'}, {seachQuery: 'the iq'}, {seachQuery: 'measure 1'},
   {seachQuery: 'measure 2'}, {seachQuery: 'measure 3'}, {seachQuery: 'measure 4'}
  ].forEach((data) => {
    it('should filter the right rows when typing \'' + data.seachQuery + '\' in the sarchbox', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
      page.allTableRows.should('have.length', 8)

      page.searchInputBox.type(data.seachQuery);
      page.allTableRows.should('have.length', 1);
    });
  });

  it('should filter the right rows when typing \'1\' in the sarchbox', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    page.searchInputBox.type('1');
    page.allTableRows.should('have.length', 7);
  });


  it('should test instruments dropdown', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

    page.instrumentsBox.select('i1');
    page.allTableRows.should('have.length', 7);

    page.instrumentsBox.select('pheno_common');
    page.allTableRows.should('have.length', 1);

    page.instrumentsBox.select('All instruments');
    page.allTableRows.should('have.length', 8);
  });

  it('should test sort', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    page.headerCells.eq(0).click();
    page.tableCells.eq(0).should('have.text', 'i1');
    page.headerCells.eq(0).click();
    page.tableCells.eq(0).should('have.text', 'pheno_common');

    page.headerCells.eq(1).click();
    page.tableRows.eq(1).get('gpf-table-view-cell').eq(1).should('have.text', 'age');
    page.headerCells.eq(1).click();
    page.tableRows.eq(1).get('gpf-table-view-cell').eq(1).should('have.text', 'sample_id');

    page.headerCells.eq(2).click();
    page.tableRows.eq(2).get('gpf-table-view-cell').eq(2).should('have.text', '');
    page.headerCells.eq(2).click();
    page.tableRows.eq(2).get('gpf-table-view-cell').eq(2).should('have.text', 'The IQ of the individual');
  });

  it('should test row values', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    let itr = 0;
    [
      'i1', 'age', 'The age of the individual (in months)', '', 'continuous [68.001, 606.229] ', '', '    ', '' // The Age PV male female column makes holds empty spans with spaces when text is missing
    ].forEach(data => {
      page.tableRows.eq(0).get('gpf-table-view-cell').eq(itr++).should('have.text', data);
    });
/*
    itr = 0;
    [
      'i1', 'iq', 'The age of the individual', '', 'continuous [68.001, 606.229] ', '', '    ', '' // The Age PV male female column makes holds empty spans with spaces when text is missing
    ].forEach(data => {
      page.tableRows.eq(1).get('gpf-table-view-cell').eq(itr++).should('have.text', data);
    });
*/
  });

  it('should test download', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    const downloadFilePath = Cypress.config('downloadsFolder');
    const expectedFilePath = 'cypress/fixtures/pheno-browser/';

    page.instrumentsBox.select('All instruments');

    cy.window().document().then(function (doc) {
      doc.addEventListener('click', () => {
        setTimeout(function () { doc.location.reload() }, 5000)
      })
      page.downloadButton.click();
    });

    cy.readFile(downloadFilePath + '/instrument.csv', { timeout: 5000 }).then(downloadedFile => {
      cy.readFile(expectedFilePath + 'instrument_all.csv', { timeout: 5000 }).then(expectedFile => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });

  });


  // add tests for:
  // icons
});
