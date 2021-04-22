import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles table tests', () => {
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesTablePage.cleanup();
    autismGeneProfilesTablePage.navigateToHome();
    autismGeneProfilesTablePage.toggleSidenav();
    autismGeneProfilesTablePage.sidenavAutismGeneProfilesButton.click();
  });

  it('should display table', () => {
    autismGeneProfilesTablePage.table.should('be.visible');
  });

  it('should display gene search bar', () => {
    autismGeneProfilesTablePage.geneSearchInput.should('be.visible');
  });

  it('should filter out genes via the gene search ', () => {
    autismGeneProfilesTablePage.geneSearchInput.type('CHD8');
    autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
  });

  it('should display gene sets columns filtering button', () => {
    autismGeneProfilesTablePage.autismGeneSetsButton.should('be.visible');
  });

  // tests for the other columns filtering buttons
});

describe('Autism gene profiles table data tests', () => {
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
    autismGeneProfilesTablePage.cleanup();
    autismGeneProfilesTablePage.navigateToHome();
    autismGeneProfilesTablePage.toggleSidenav();
    autismGeneProfilesTablePage.sidenavAutismGeneProfilesButton.click();
  });

  [{geneSymbol: 'CHD8', expectedRow: ['CHD8', '✓', '', '', '', '1', '193', '-2.34', '1', '193', '-2.34', '7', '', '', '', '', '']}
  ].forEach((data) => {
    it(`should display correct gene data for ${data.geneSymbol}`, () => {
      autismGeneProfilesTablePage.geneSearchInput.type(data.geneSymbol);
      autismGeneProfilesTablePage.allTableRows.should('have.length', 1);
      
      for(let cellIndex = 0; cellIndex < data.expectedRow.length; cellIndex++) {
        autismGeneProfilesTablePage.allTableRows.find('td').eq(cellIndex).invoke('text').then(text => {
          expect(text.trim()).to.eq(data.expectedRow[cellIndex]);
        });
      }
    });
  });
});

describe('Column filtering dropdown tests', () => {
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  beforeEach(() => {
    autismGeneProfilesTablePage.navigateToHome();
    autismGeneProfilesTablePage.toggleSidenav();
    autismGeneProfilesTablePage.sidenavAutismGeneProfilesButton.click();
    autismGeneProfilesTablePage.autismGeneSetsButton.click();
  });

  it('should open autism gene sets dropdown after clicking on the autism gene sets columns filtering button', () => {
    autismGeneProfilesTablePage.autismGeneSetsDropdown.should('be.visible');
  });

  it('should open gene sets dropdown and display the check/uncheck all button', () => {
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.should('be.visible');
  });

  it('should open gene sets dropdown and display the search input box', () => {
    autismGeneProfilesTablePage.autismGeneSetsDropdownSearch.should('be.visible');
  });

  it('should open gene sets dropdown and display the appply button', () => {
    autismGeneProfilesTablePage.autismGeneSetsDropdownApplyButton.should('be.visible');
  });

  it('should open gene sets dropdown, check/uncheck all checkboxes and disable the apply button accordingly', () => {
    autismGeneProfilesTablePage.autismGeneSetsDropdownApplyButton.should('be.enabled');

    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.autismGeneSetsDropdownApplyButton.should('not.be.enabled');

    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.autismGeneSetsDropdownApplyButton.should('be.enabled');
  });

  it('should check/uncheck all gene sets column filtering options using the check/uncheck all button', () => {
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('not.be.checked');
    });
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });

  it('should change the check/uncheck button text', () => {
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');

    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Check all');

    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.autismGeneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');
  });

  it('should filter gene sets dropdown options using the search', () => {
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.should('have.length', 4);
    autismGeneProfilesTablePage.autismGeneSetsDropdownSearch.type('autism');
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.should('have.length', 1);
  });

  // apply should actually work and make columns disappear/add

  // sorting should work

  // sorting arrow should change the image when clicked
});
