import { AutismGeneProfilesBlock } from 'cypress/elements/autism-gene-profiles-block-page';
import { AutismGeneProfilesSingleView } from 'cypress/elements/autism-gene-profiles-single-view-page';
import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('Autism gene profiles block tests', () => {
  const page = new AutismGeneProfilesBlock();
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();
  const autismGeneProfilesSingleView = new AutismGeneProfilesSingleView();

  before(() => {
    page.cleanup();
  });

  beforeEach(() => {
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.autismGeneProfiles);
  });

  it('should display tabs navbar', () => {
    page.navbar.should('be.visible');
  });

  it('should display autism gene profiles table', () => {
    autismGeneProfilesTablePage.window.should('be.visible');
  });

  it('should create and navigate to the new tab after clicking the first gene link', () => {
    page.allTabs.should('have.length', 1);
    autismGeneProfilesTablePage.table.should('be.visible');
    autismGeneProfilesSingleView.window.should('not.exist');

    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.table.should('not.be.visible');
    autismGeneProfilesSingleView.window.should('be.visible');
  });

  it('should close the tab after clicking on the x button and navigate to the home tab', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.table.should('not.be.visible');
    autismGeneProfilesSingleView.window.should('be.visible');
  
    autismGeneProfilesTablePage.firstTabCloseButton.click();
    page.allTabs.should('have.length', 1);
    autismGeneProfilesTablePage.table.should('be.visible');
    autismGeneProfilesSingleView.window.should('not.exist');
  });

  it('should close the current tab after pressing the \'w\' shortcut and navigate to the home tab', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.table.should('not.be.visible');
    autismGeneProfilesSingleView.window.should('be.visible');

    cy.get('body').type('w');
    page.allTabs.should('have.length', 1);
    autismGeneProfilesTablePage.table.should('be.visible');
    autismGeneProfilesSingleView.window.should('not.exist');
  });

  it('should click on gene that has already been opened and navigate to it\'s tab', () => {
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.allTabs.should('have.length', 2);
    autismGeneProfilesTablePage.table.should('not.be.visible');
    autismGeneProfilesSingleView.window.should('be.visible');
  });

  /* 
    Using `autismGeneProfilesTablePage.allTableRows.should('have.length', 1);`
    instead of cy.wait doesn't work?
    fix me
  */
  it('should create multiple tabs and navigate through them using the number keybinds', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();

    autismGeneProfilesTablePage.geneSearchInput.clear();
    autismGeneProfilesTablePage.geneSearchInput.type('SHANK2');
    cy.wait(1000);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();

    autismGeneProfilesTablePage.geneSearchInput.clear();
    autismGeneProfilesTablePage.geneSearchInput.type('LAMA3');
    cy.wait(1000);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();

    autismGeneProfilesTablePage.geneSearchInput.clear();
    autismGeneProfilesTablePage.geneSearchInput.type('TTLL12');
    cy.wait(1000);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();

    autismGeneProfilesTablePage.geneSearchInput.clear();
    autismGeneProfilesTablePage.geneSearchInput.type('POLL');
    cy.wait(1000);
    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();

    autismGeneProfilesTablePage.geneSearchInput.clear();
    autismGeneProfilesTablePage.geneSearchInput.type('CHGA');
    cy.wait(1000);

    autismGeneProfilesTablePage.firstGeneInTable.click();
    page.homeTab.click();
    page.allTabs.should('have.length', 7);

    cy.get('body').type('2');
    autismGeneProfilesSingleView.header.eq(0).should('be.visible');
    autismGeneProfilesSingleView.header.eq(0).should('have.text', 'CHD8');

    cy.get('body').type('3');
    autismGeneProfilesSingleView.header.eq(1).should('be.visible');
    autismGeneProfilesSingleView.header.eq(1).should('have.text', 'SHANK2');

    cy.get('body').type('4');
    autismGeneProfilesSingleView.header.eq(2).should('be.visible');
    autismGeneProfilesSingleView.header.eq(2).should('have.text', 'LAMA3');

    cy.get('body').type('5');
    autismGeneProfilesSingleView.header.eq(3).should('be.visible');
    autismGeneProfilesSingleView.header.eq(3).should('have.text', 'TTLL12');

    cy.get('body').type('6');
    autismGeneProfilesSingleView.header.eq(4).should('be.visible');
    autismGeneProfilesSingleView.header.eq(4).should('have.text', 'POLL');

    cy.get('body').type('7');
    autismGeneProfilesSingleView.header.eq(5).should('be.visible');
    autismGeneProfilesSingleView.header.eq(5).should('have.text', 'CHGA');

    page.homeTab.click();
    autismGeneProfilesTablePage.table.should('be.visible');
    autismGeneProfilesSingleView.window.should('not.be.visible');
  });

  it.only('should highlight rows and then use the clear keybind', () => {
    [1, 2, 3].forEach(id => {
      cy.get(`tbody.ng-star-inserted > :nth-child(${id}) > :nth-child(2)`).click({ctrlKey:true});        
    });
    [1, 2, 3].forEach(id => {
      cy.get(`tbody.ng-star-inserted > :nth-child(${id})`).should('satisfy', row => {
        const classList = Array.from(row[0].classList);
        return classList.includes('row-highlight');
      });
    });
    cy.get('body').type('{esc}');
    [1, 2, 3].forEach(id => {
      cy.get(`tbody.ng-star-inserted > :nth-child(${id})`).should('satisfy', row => {
        const classList = Array.from(row[0].classList);
        return !classList.includes('row-highlight');
      });
    });
  });
});
