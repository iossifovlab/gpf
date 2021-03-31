import { PhenoBrowserPage } from 'cypress/elements/pheno-browser-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Pheno browser tests', () => {
  const phenoBrowserPage = new PhenoBrowserPage();

  before(() => {
    phenoBrowserPage.navigateToHome();
    phenoBrowserPage.loginAdmin();
  });

  after(() => {
    phenoBrowserPage.logout();
  });

  beforeEach(() => {
    phenoBrowserPage.navigateToHome();
    Cypress.Cookies.preserveOnce('sessionid');
  });

  [{seachQuery: 'the age'}, {seachQuery: 'the iq'}, {seachQuery: 'measure 1'},
   {seachQuery: 'measure 2'}, {seachQuery: 'measure 3'}, {seachQuery: 'measure 4'}
  ].forEach((data) => {
    it('should have working search box when filtering with \'' + data.seachQuery + '\' search query', () => {
      phenoBrowserPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeBrowser);
      phenoBrowserPage.allTableRows.should('have.length', 8)

      phenoBrowserPage.searchInputBox.type(data.seachQuery);
      phenoBrowserPage.allTableRows.should('have.length', 1)
    });
  });

  it('should display the right amount of table rows when the query in the search box is \'1\'', () => {
    phenoBrowserPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.phenotypeBrowser);
    phenoBrowserPage.searchInputBox.type('1');
    phenoBrowserPage.allTableRows.should('have.length', 7)
  });
});
