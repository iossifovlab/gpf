import { GenomicScoresBlockPage } from 'cypress/elements/genomic-scores-block-page';
import { datasetIds, toolPageNames } from 'cypress/elements/utils';

describe('Genomic scores panel tests', () => {
  const genomicScoresBlockPage = new GenomicScoresBlockPage();

  before(() => {
    genomicScoresBlockPage.cleanup();
    genomicScoresBlockPage.navigateToHome();
    genomicScoresBlockPage.loginAdmin();
  });

  beforeEach(() => {
    genomicScoresBlockPage.preserveLogin();
    genomicScoresBlockPage.navigateToHome();
  });

  it('should display genomic scores panel after \'add filter\' button click ' +
     'and remove it after \'remove filter\' button click', () => {
    genomicScoresBlockPage.navigateToDatasetPage(datasetIds.compAll, toolPageNames.genotypeBrowser);
    genomicScoresBlockPage.panel.should('not.exist');

    genomicScoresBlockPage.addFilterButton.click();
    genomicScoresBlockPage.panel.should('be.visible');

    genomicScoresBlockPage.removeFilterButton.click();
    genomicScoresBlockPage.panel.should('not.exist');
  });
});

