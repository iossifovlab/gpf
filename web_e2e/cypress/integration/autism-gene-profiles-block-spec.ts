import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles table tests', () => {
  const autismGeneProfilesBlockPage = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesBlockPage.cleanup();
  });

  beforeEach(() => {
    autismGeneProfilesBlockPage.navigateToHome();
    autismGeneProfilesBlockPage.toggleSidenav();
    autismGeneProfilesBlockPage.sidenavAutismGeneProfilesButton.click();
  });

  it('should display tabs navbar', () => {
    autismGeneProfilesBlockPage.navbar.should('be.visible');
  });

  it('should display autism gene profiles table', () => {
    autismGeneProfilesTablePage.window.should('be.visible');
  });

  it('should create new tab after clicking the first gene link', () => {
    autismGeneProfilesBlockPage.allTabs.should('have.length', 1);
    autismGeneProfilesTablePage.firstGeneLink.click();
    autismGeneProfilesBlockPage.allTabs.should('have.length', 2);
  });

  it('should close the tab after clicking on the x button', () => {
    autismGeneProfilesTablePage.firstGeneLink.click();
    autismGeneProfilesTablePage.firstTabCloseButton.click();
    autismGeneProfilesBlockPage.allTabs.should('have.length', 1);
  });

  it('should close the current tab after pressing the \'w\' shortcut', () => {
    autismGeneProfilesTablePage.firstGeneLink.click();
    cy.get('body').type('w');
    autismGeneProfilesBlockPage.allTabs.should('have.length', 1);
  });
});
