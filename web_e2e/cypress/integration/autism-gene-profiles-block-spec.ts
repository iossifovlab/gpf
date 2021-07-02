import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.toggleSidenav();
    page.sidenavAutismGeneProfilesButton.click();
  });

  it('should display tabs navbar', () => {
    page.navbar.should('be.visible');
  });

  it('should display autism gene profiles table', () => {
    autismGeneProfilesTablePage.window.should('be.visible');
  });

  it('should create new tab after clicking the first gene link', () => {
    page.allTabs.should('have.length', 1);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
  });

  it('should close the tab after clicking on the x button', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.firstTabCloseButton.click();
    page.allTabs.should('have.length', 1);
  });

  it('should close the current tab after pressing the \'w\' shortcut', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    cy.get('body').type('w');
    page.allTabs.should('have.length', 1);
  });

  // more tabs tests
});


// describe('general tests', () => {
//   const page = new AutismGeneProfilesBlock();
//   const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

//   before(() => {
//     page.cleanup();
//   });

//   beforeEach(() => {
//     page.navigateToHome();
//     page.toggleSidenav();
//     page.sidenavAutismGeneProfilesButton.click();
//   });

//  // red lines tests - check the values also check the difference between 0 and undefind
//  // gene sets check in the table should match the one in the single view
//  // protection/autism scores in the table should match the ones in the single view

// });
