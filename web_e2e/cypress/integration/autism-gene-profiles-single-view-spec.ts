import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles single view tests', () => {
  const autismGeneProfilesSingleViewPage = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesSingleViewPage.cleanup();
    autismGeneProfilesSingleViewPage.navigateToHome();
    autismGeneProfilesSingleViewPage.toggleSidenav();
    autismGeneProfilesSingleViewPage.sidenavAutismGeneProfilesButton.click();
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.allTableCells.first().click();
  });

  it('should display header', () => {
    autismGeneProfilesSingleViewPage.header.should('be.visible');
    autismGeneProfilesSingleViewPage.header.should('have.text', 'CHD8');
  });

  it('should display gene browser link', () => {
    autismGeneProfilesSingleViewPage.geneBrowserLink.should('be.visible');
    autismGeneProfilesSingleViewPage.geneBrowserLink.should('have.text', ' View CHD8 in the Gene Browser ');
  });

  it('should have the correct href on the gene browser link', () => {
    autismGeneProfilesSingleViewPage.header.invoke('text').then((headerText) => {
      const baseUrl = Cypress.config().baseUrl;
      const headerName = headerText;
      const geneBrowserUrl = `${baseUrl}datasets/ALL_genotypes/gene-browser/${headerName}`;
      autismGeneProfilesSingleViewPage.geneBrowserLink.should('have.prop', 'href')
        .and('equal', geneBrowserUrl)
    });
  });

  it('should display the autism scores table', () => {
    autismGeneProfilesSingleViewPage.autismScoresTable.should('be.visible');
    autismGeneProfilesSingleViewPage.autismScoresTable.find('th').should('have.text', 'Autism Scores');
    autismGeneProfilesSingleViewPage.autismScoresTable.find('tr').should('have.length', 1);
  });

  it('should display the protection scores table', () => {
    autismGeneProfilesSingleViewPage.protectionScoresTable.should('be.visible');
    autismGeneProfilesSingleViewPage.protectionScoresTable.find('th').should('have.text', 'Protection Scores');
    autismGeneProfilesSingleViewPage.protectionScoresTable.find('tr').should('have.length', 4);
  });

  it('should display the single scores markers', () => {
    autismGeneProfilesSingleViewPage.singleScoreMarkers.should('have.length', 5);
  });

  it('should display the autism gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneAutismGeneSetsTable.should('be.visible');
    autismGeneProfilesSingleViewPage.geneAutismGeneSetsTable.find('th').should('have.text', 'Autism Gene Sets');
    autismGeneProfilesSingleViewPage.geneAutismGeneSetsTable.find('tr').should('have.length', 2);
  });

  it('should display the relevant gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.should('be.visible');
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.find('th').should('have.text', 'Relevant Gene Sets');
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.find('tr').should('have.length', 4);
  });

  it('should display the relevant gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.should('be.visible');
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.find('th').should('have.text', 'Relevant Gene Sets');
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.find('tr').should('have.length', 4);
  });

  it('should display the datasets table', () => {
    autismGeneProfilesSingleViewPage.datasetsTable.should('be.visible');
    autismGeneProfilesSingleViewPage.datasetsTable.find('th').first().should('have.text', 'IossifovWE2014');
    autismGeneProfilesSingleViewPage.datasetsTable.find('tr').should('have.length', 3);
  });

  it('should display the external links table', () => {
    autismGeneProfilesSingleViewPage.externalLinksTable.should('be.visible');
    autismGeneProfilesSingleViewPage.externalLinksTable.find('th').should('have.text', 'External links');
    autismGeneProfilesSingleViewPage.externalLinksTable.find('tr').should('have.length', 3);
  });
});

// add data tests describe
