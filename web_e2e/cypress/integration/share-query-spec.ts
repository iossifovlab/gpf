import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { ShareQueryPage } from 'cypress/elements/share-query-page';
import { datasetIds, toolPageLinks } from 'cypress/elements/utils';

describe('Share query tests', () => {
  const page = new ShareQueryPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
  });

  it('should open share query dropdown menu after share query button click', () => {
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
  });

  it('should open share query menu and check if it displays the input field and the copy button', () => {
    page.copyButton.should('not.be.visible');
    page.input.should('not.be.visible')

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
    page.copyButton.should('be.visible');
    page.input.should('be.visible');
  });

  it('should open share query menu, click on the copy button and check whether the text changes properly', () => {
    page.copyButton.should('not.be.visible');
    page.input.should('not.be.visible')

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
    page.copyButton.should('have.text', 'Copy');

    page.copyButton.click();
    page.copyButton.should('have.text', 'Copied');

    page.copyButton.should('have.text', 'Copy');
  });

  it('should share a query, load it and open all tools tabs', () => {
    const datasetsPage = new DatasetsPage();

    page.button.should('be.visible');
    page.button.click();
    page.input.invoke('val').then(url => cy.visit(String(url)));

    page.datasetsDropdownMenuButton.should('have.text', 'comp_all');
    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.genotypeBrowserButton.should('be.visible');
    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.phenotypeBrowserButton.should('be.visible');
    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.phenotypeToolButton.should('be.visible');
    datasetsPage.phenotypeToolButton.click();
    datasetsPage.geneBrowserButton.should('be.visible');
    datasetsPage.geneBrowserButton.click();
  });

  it('should navigate to genotype browser, check all effect types checkboxes, generate a share query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    genotypeBlockPage.findButtonInComponentContainingText('.effect-card input, .effect-card button', 'All').click();

    page.button.should('be.visible');
    page.button.click();
    page.input.invoke('val').then(url => cy.visit(String(url)));
    genotypeBlockPage.findAllCheckboxesInComponent('.effect-card').each(element => {
      cy.wrap(element).should('be.visible');
      cy.wrap(element).should('be.checked');
    });
  });
});
