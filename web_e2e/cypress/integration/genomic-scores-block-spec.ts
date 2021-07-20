import { GenomicScoresBlockPage } from 'cypress/elements/genomic-scores-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genomic scores panel tests', () => {
  const page = new GenomicScoresBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display genomic scores panel after \'add filter\' button click ' +
     'and remove it after \'remove filter\' button click', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.panel.should('not.exist');

    page.addFilterButton.click();
    page.panel.should('be.visible');

    page.removeFilterButton.click();
    page.panel.should('not.exist');
  });
});

