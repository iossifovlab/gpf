import { DatasetsPage } from 'cypress/elements/datasets-page';
import { GenotypeBlockPage } from 'cypress/elements/genotype-block-page';
import { SaveQueryPage } from 'cypress/elements/save-query-page';
import { SavedQueriesPage } from 'cypress/elements/saved-queries-page';
import { datasetIds, sidenavPageLinks, toolPageLinks } from 'cypress/elements/utils';

// to remove 'skip'
describe.skip('Save query common tests', () => {
  const page = new SaveQueryPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');
    page.button.click();
  });

  it('should display link input', () => {
    page.linkInput.should('be.visible');
  });

  it('should display copy link button', () => {
    page.copyLinkButton.should('be.visible');
  });

  it('should display name input', () => {
    page.nameInput.should('be.visible');
  });

  it('should display description input', () => {
    page.descriptionInput.should('be.visible');
  });

  it('should display save button', () => {
    page.saveButton.should('be.visible');
  });
});

// to remove 'skip'
describe.skip('Save query tests', () => {
  const page = new SaveQueryPage();
  const savedQueriesPage = new SavedQueriesPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
  });

  it('should open save query dropdown menu after pressing "Share/save query" button', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu');

    page.button.click();
    page.dropdownMenu.invoke('attr', 'class').should('contain', 'dropdown-menu show');
  });

  it('should open save query dropdown menu, click on the copy link button ' +
     'and check whether the "Copied!" tooltip appears', () => {
    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.button.click();
    page.copyLinkButton.should('be.visible');

    page.copiedTooltip.should('not.exist');
    page.copyLinkButton.click();
    page.copiedTooltip.should('be.visible');
  });

  it('should save a query, load it, open all tools tabs and delete the query', () => {
    const datasetsPage = new DatasetsPage();
    cy.intercept('POST', '/gpf/api/v3/user_queries/save').as('save');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    page.button.click();
    page.nameInput.type('TestLoadAndDeleteQuery');
    page.saveButton.click();
    cy.wait('@save');

    page.navigateToSidenavPage(sidenavPageLinks.userProfile);
    savedQueriesPage.queryNameCell('genotype-browser', 'TestLoadAndDeleteQuery').should('be.visible');
    savedQueriesPage.queryLoadButton('genotype-browser', 'TestLoadAndDeleteQuery').click();

    datasetsPage.datasetStatisticsButton.click();
    datasetsPage.waitForPageToLoad(toolPageLinks.datasetStatistics);
    datasetsPage.genotypeBrowserButton.click();
    datasetsPage.waitForPageToLoad(toolPageLinks.genotypeBrowser);
    datasetsPage.phenotypeBrowserButton.click();
    datasetsPage.waitForPageToLoad(toolPageLinks.phenotypeBrowser);
    datasetsPage.phenotypeToolButton.click();
    datasetsPage.waitForPageToLoad(toolPageLinks.phenotypeTool);
    datasetsPage.geneBrowserButton.click();
    datasetsPage.waitForPageToLoad(toolPageLinks.geneBrowser);

    page.navigateToSidenavPage(sidenavPageLinks.userProfile);
    savedQueriesPage.queryDeleteButton('genotype-browser', 'TestLoadAndDeleteQuery').click();
    savedQueriesPage.queryNameCell('genotype-browser', 'TestLoadAndDeleteQuery').should('not.exist');
  });

  it('should navigate to genotype browser, check all effect types checkboxes, save a query, ' +
     'load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();
    cy.intercept('POST', '/gpf/api/v3/user_queries/save').as('save');

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('gpf-effect-types', 'All').click();
    page.button.click();
    page.nameInput.type('CheckSavedQuery');
    page.saveButton.click();
    cy.wait('@save');

    page.navigateToSidenavPage(sidenavPageLinks.userProfile);
    savedQueriesPage.queryLoadButton('genotype-browser', 'CheckSavedQuery').click();
    genotypeBlockPage.findAllCheckboxesInComponent('gpf-effect-types').each(element => {
      cy.wrap(element).should('be.visible');
      cy.wrap(element).should('be.checked');
    });

    page.navigateToSidenavPage(sidenavPageLinks.userProfile);
    savedQueriesPage.queryDeleteButton('genotype-browser', 'CheckSavedQuery').click();
  });

  it('should navigate to genotype browser, check all effect types checkboxes, click on "Save/share query" button, ' +
     'copy the share link, load it and validate that all effect types checkboxes are checked', () => {
    const genotypeBlockPage = new GenotypeBlockPage();

    page.navigateToDatasetPage(datasetIds.compAll, toolPageLinks.genotypeBrowser);
    genotypeBlockPage.findButtonInComponentContainingText('.effect-card input, .effect-card button', 'All').click();

    page.button.should('be.visible');
    page.button.click();

    page.linkInput.invoke('val').then(url => {
      cy.visit(String(url));
      page.waitForPageToLoad(toolPageLinks.genotypeBrowser);
    });

    genotypeBlockPage.findAllCheckboxesInComponent('.effect-card').each(element => {
      cy.wrap(element).should('be.visible');
      cy.wrap(element).should('be.checked');
    });
  });
});
