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

  it('should have working table header sorting buttons', () => {
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

  const dataArray = [
    'i1ageThe age of the individual (in months)continuous[68.001,606.229]',
    'i1iqThe IQ of the individualcontinuous[-1.111e+1,174.290]',
    'i1m1Measure 1, a normally distributed continuous measure with a mean of 80continuous[28.877,143.029]0.97110.25120.02990.6413',
    'i1m2Measure 2, a normally distributed continuous measure with a mean of 40continuous[17.650,69.721]0.43890.42630.55470.3443',
    'i1m3Measure 3, a continuous measure with a normal distribution with mean of 80 for non-affected individuals, and 40 for affected individualscontinuous[20.349,122.832]0.11730.62940.05560.0393',
    'i1m4Measure 4, an ordinal measure with a Poisson distribution with an average number of events per interval of 4 for non-affected individuals, and 1 for affected individualscontinuous[0.000,10.000]0.32060.32320.94930.5862',
    'i1m5Measure 5, a categorical measure with random distribution of 5 distinct valuescategorical[val1][val2][val3][val4][val5]',
    'pheno_commonsample_idraw[f1.dad][f1.mom][f1.p1][f1.s1][f2.dad][f2.mom][f2.p1][f2.s1][f3.dad][f3.mom][f3.p1][f3.s1][f4.dad][f4.mom][f4.p1][f4.s1][f5.dad][f5.mom][f5.p1][f5.s1]'
  ]
  for (let i = 0; i < dataArray.length; i++) {
    it('should have the correct values in the row with index ' + String(i), () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);

      const expectedRowText = dataArray[i];
      page.tableRows.eq(i).should('have.text', expectedRowText);
    });
  }

  it('should download all instruments and validate whether they are equal to the reference data', () => {
    const downloadFilePath = Cypress.config('downloadsFolder') + '/instrument.csv';
    const expectedFilePath = 'cypress/fixtures/pheno-browser/instrument_all.csv';

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    page.instrumentsBox.select('All instruments');

    cy.window().document().then(function(doc) {
      doc.addEventListener('click', () => {
        setTimeout(function() { doc.location.reload() }, 5000)
      })
      page.downloadInstrumentsButton.click();
    });

    cy.readFile(downloadFilePath, { timeout: 5000 }).then(downloadedFile => {
      cy.readFile(expectedFilePath, { timeout: 5000 }).then(expectedFile => {
        const downloadedFileLines = downloadedFile.split(/\r\n|\r|\n/);
        const expectedFileLines = expectedFile.split(/\r\n|\r|\n/);
        expect(downloadedFileLines).to.deep.eq(expectedFileLines);
      });
    });
  });
});
