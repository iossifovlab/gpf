import { GenomicScoresBlockPage } from 'cypress/elements/genomic-scores-block-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Genomic scores panel tests', () => {
  const page = new GenomicScoresBlockPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should display genomic scores panel after "add filter" button click ' +
     'and remove it after "remove filter" button click', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.panel.should('not.exist');

    page.addFilterButton.click();
    page.panel.should('be.visible');

    page.removeFilterButton.click();
    page.panel.should('not.exist');
  });

  it.only('should enter filter data and check how it affects the histogram', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);

    page.addFilterButton.click();
    page.fromInputField.eq(0).clear().type('0.3').type('{enter}');
    page.histogramRangeSelectors.eq(0).should('have.text', '~21727789 (32.46%)');

    page.toInputField.eq(0).clear().type('1.45').type('{enter}');
    page.histogramRangeSelectors.eq(1).should('have.text', '~9402408 (14.05%)');
    page.histogramRangeSelectors.eq(2).should('have.text', '~35798106 (53.49%)');

    page.addFilterButton.click();
    page.filterSelect.eq(1).select('CADD raw');
    page.fromInputField.eq(1).clear().type('9.7944').type('{enter}');
    page.histogramRangeSelectors.eq(3).should('have.text', '~8591392889 (99.97%)');

    page.toInputField.eq(1).clear().type('13.6935').type('{enter}');
    page.histogramRangeSelectors.eq(4).should('have.text', '~637710 (0.01%)');
    page.histogramRangeSelectors.eq(5).should('have.text', '~2325073 (0.03%)');

    page.removeFilterButton.eq(0).click();
    page.histogramRangeSelectors.eq(0).should('have.text', '~8591392889 (99.97%)');
    page.histogramRangeSelectors.eq(1).should('have.text', '~637710 (0.01%)');
    page.histogramRangeSelectors.eq(2).should('have.text', '~2325073 (0.03%)');

    page.removeFilterButton.eq(0).click();
  });
});
