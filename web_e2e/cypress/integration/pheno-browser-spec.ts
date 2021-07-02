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
    it('should have working search box when filtering with \'' + data.seachQuery + '\' search query', () => {
      page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
      page.allTableRows.should('have.length', 8)

      page.searchInputBox.type(data.seachQuery);
      page.allTableRows.should('have.length', 1)
    });
  });

  it('should display the right amount of table rows when the query in the search box is \'1\'', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.phenotypeBrowser);
    page.searchInputBox.type('1');
    page.allTableRows.should('have.length', 7)
  });
});
