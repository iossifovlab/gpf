import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe.only('Autism gene profiles single view tests', () => {
  const autismGeneProfilesSingleViewPage = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesSingleViewPage.cleanup();
    autismGeneProfilesSingleViewPage.navigateToHome();
    autismGeneProfilesSingleViewPage.toggleSidenav();
    autismGeneProfilesSingleViewPage.sidenavAutismGeneProfilesButton.click();
    autismGeneProfilesTablePage.firstGeneLink.click();
  });

  it('should display header', () => {
    autismGeneProfilesSingleViewPage.header.should('be.visible');
  });

  it('should display gene browser link', () => {
    autismGeneProfilesSingleViewPage.geneBrowserLink.should('be.visible');
  });

  it('should display the autism scores table', () => {
    autismGeneProfilesSingleViewPage.autismScoresTable.should('be.visible');
  });

  it('should display the protection scores table', () => {
    autismGeneProfilesSingleViewPage.protectionScoresTable.should('be.visible');
  });

  it('should display the autism gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneAutismGeneSetsTable.should('be.visible');
  });

  it('should display the relevant gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneRelevantGeneSetsTable.should('be.visible');
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

  // red market number indicator test
});
