import { BasePage } from './utils';

export class AutismGeneProfilesTable extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profiles-table');
  }

  get table() {
    return cy.get('table');
  }

  get geneSearchInput() {
    return cy.get('#gene-search-input');
  }

  get allTableRows() {
    return cy.get('table tbody tr');
  }

  get geneSetsButton() {
    return cy.get('#gene-sets-button');
  }

  get geneSetsDropdown() {
    return cy.get('#gene-sets-dropdown');
  }

  get geneSetsCheckUncheckAllButton() {
    return this.geneSetsDropdown.find('#check-uncheck-all-button');
  }

  get geneSetsDropdownSearch() {
    return this.geneSetsDropdown.find('input[name="search"]');
  }

  get geneSetsDropdownApplyButton() {
    return this.geneSetsDropdown.contains('Apply');
  }

  get allGeneSetsDropdownCheckboxes() {
    return cy.get('gpf-multiple-select-menu#gene-sets-dropdown label input');
  }

  get autismScoresButton() {
    return cy.get('#autism-scores-button');
  }

  get autismScoresDropdown() {
    return cy.get('#autism-scores-dropdown');
  }

  get protectionScoresButton() {
    return cy.get('#protection-scores-button');
  }

  get protectionScoresDropdown() {
    return cy.get('#protection-scores-dropdown');
  }

  get firstGeneLink() {
    return cy.get('tbody td').first();
  }

  get firstTabCloseButton() {
    return cy.get('nav span').first();
  }
}
