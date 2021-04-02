import { AutismGeneProfilesTable } from 'cypress/elements/autism-gene-profiles-table-page';

describe('Autism gene profiles table tests', () => {
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  before(() => {
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
    autismGeneProfilesTablePage.geneSetsButton.should('be.visible');
  });

  it('should open gene sets dropdown after clicking on gene sets columns filtering button', () => {
    autismGeneProfilesTablePage.geneSetsDropdown.should('not.be.visible');
    autismGeneProfilesTablePage.geneSetsButton.click();
    autismGeneProfilesTablePage.geneSetsDropdown.should('be.visible');
  });

  it('should display autism scores columns filtering button', () => {
    autismGeneProfilesTablePage.autismScoresButton.should('be.visible');
  });

  it('should open autism scores dropdown after clicking on autism scores columns filtering button', () => {
    autismGeneProfilesTablePage.autismScoresDropdown.should('not.be.visible');
    autismGeneProfilesTablePage.autismScoresButton.click();
    autismGeneProfilesTablePage.autismScoresDropdown.should('be.visible');
  });

  it('should display protection scores columns filtering button', () => {
    autismGeneProfilesTablePage.protectionScoresButton.should('be.visible');
  });

  it('should open protection scores dropdown after clicking on protection scores columns filtering button', () => {
    autismGeneProfilesTablePage.protectionScoresDropdown.should('not.be.visible');
    autismGeneProfilesTablePage.protectionScoresButton.click();
    autismGeneProfilesTablePage.protectionScoresDropdown.should('be.visible');
  });
});

describe('Column filtering dropdown tests', () => {
  const autismGeneProfilesTablePage = new AutismGeneProfilesTable();

  beforeEach(() => {
    autismGeneProfilesTablePage.navigateToHome();
    autismGeneProfilesTablePage.toggleSidenav();
    autismGeneProfilesTablePage.sidenavAutismGeneProfilesButton.click();
    autismGeneProfilesTablePage.geneSetsButton.click();
  });

  it('should open gene sets dropdown after clicking on gene sets columns filtering button', () => {
    autismGeneProfilesTablePage.geneSetsDropdown.should('be.visible');
    autismGeneProfilesTablePage.geneSetsButton.click();
    autismGeneProfilesTablePage.geneSetsDropdown.should('not.be.visible');
  });

  it('should open gene sets dropdown and display the check/uncheck all button', () => {
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.should('be.visible');
  });

  it('should open gene sets dropdown and display the search input box', () => {
    autismGeneProfilesTablePage.geneSetsDropdownSearch.should('be.visible');
  });

  it('should open gene sets dropdown and display the appply button', () => {
    autismGeneProfilesTablePage.geneSetsDropdownApplyButton.should('be.visible');
  });

  it('should open gene sets dropdown, check/uncheck all checkboxes and disable the apply button accordingly', () => {
    autismGeneProfilesTablePage.geneSetsDropdownApplyButton.should('be.enabled');

    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.geneSetsDropdownApplyButton.should('not.be.enabled');

    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.geneSetsDropdownApplyButton.should('be.enabled');
  });

  it('should check/uncheck all gene sets column filtering options using the check/uncheck all button', () => {
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('not.be.checked');
    });
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.each((element) => {
      cy.wrap(element).should('be.checked');
    });
  });

  it('should change the check/uncheck button text', () => {
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');

    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.should('have.text', 'Check all');

    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.click();
    autismGeneProfilesTablePage.geneSetsCheckUncheckAllButton.should('have.text', 'Uncheck all');
  });

  it('should filter gene sets dropdown options using the search', () => {
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.should('have.length', 4);
    autismGeneProfilesTablePage.geneSetsDropdownSearch.type('autism');
    autismGeneProfilesTablePage.allGeneSetsDropdownCheckboxes.should('have.length', 1);
  });
});
