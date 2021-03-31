import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles single view tests', () => {
  const autismGeneProfilesSingleViewPage = new AutismGeneProfilesSingleView();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesSingleViewPage.navigateToHome();
    autismGeneProfilesSingleViewPage.toggleSidenav();
    autismGeneProfilesSingleViewPage.sidenavAutismGeneProfilesButton.click();
    autismGeneProfilesTablePage.firstGeneLink.click();
  });

  it('should display header', () => {
    autismGeneProfilesSingleViewPage.header.should('be.visible');
  });

  it('should display gene view link', () => {
    autismGeneProfilesSingleViewPage.geneBrowserLink.should('be.visible');
  });

  it('should display autism scores table', () => {
    autismGeneProfilesSingleViewPage.autismScoresTable.should('be.visible');
  });

  it('should display protection scores table', () => {
    autismGeneProfilesSingleViewPage.protectionScoresTable.should('be.visible');
  });

  it('should display gene sets table', () => {
    autismGeneProfilesSingleViewPage.geneSetsTable.should('be.visible');
  });

  // review
  // see if you can get header element text as a getter in the elements.ts files
  it('should navigate properly navigate to the gene browser using the gene browser link', () => {
    autismGeneProfilesSingleViewPage.header.then((headerEle) => {
      const baseUrl = Cypress.config().baseUrl;
      const headerName = headerEle.text();
      const geneBrowserUrl = `${baseUrl}/datasets/iossifov_2014/geneBrowser/${headerName}`;

      autismGeneProfilesSingleViewPage.geneBrowserLink.should('have.prop', 'href')
        .and('equal', geneBrowserUrl)
    });
  });
});
