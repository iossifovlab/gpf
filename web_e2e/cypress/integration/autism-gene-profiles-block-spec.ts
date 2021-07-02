import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles block tests', () => {
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
    autismGeneProfilesTablePage.firstGeneInTable.click();
    autismGeneProfilesBlockPage.allTabs.should('have.length', 2);
  });

  it('should close the tab after clicking on the x button', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    autismGeneProfilesBlockPage.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.firstTabCloseButton.click();
    autismGeneProfilesBlockPage.allTabs.should('have.length', 1);
  });

  it('should close the current tab after pressing the \'w\' shortcut', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    cy.get('body').type('w');
    autismGeneProfilesBlockPage.allTabs.should('have.length', 1);
  });

  // more tabs tests
});


// describe('general tests', () => {
//   const autismGeneProfilesBlockPage = new AutismGeneProfilesBlock();
//   const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

//   before(() => {
//     autismGeneProfilesBlockPage.cleanup();
//   });

//   beforeEach(() => {
//     autismGeneProfilesBlockPage.navigateToHome();
//     autismGeneProfilesBlockPage.toggleSidenav();
//     autismGeneProfilesBlockPage.sidenavAutismGeneProfilesButton.click();
//   });

//  // red lines tests - check the values also check the difference between 0 and undefind
//  // gene sets check in the table should match the one in the single view
//  // protection/autism scores in the table should match the ones in the single view

// });
