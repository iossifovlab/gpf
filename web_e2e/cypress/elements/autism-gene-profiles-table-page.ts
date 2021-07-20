import { BasePage } from './utils';

export class AutismGeneProfilesTable extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profiles-table');
  }

  get table() {
    return cy.get('table');
  }

  get allTableCells() {
    return cy.get('tbody td');
  }

  get allTableRows() {
    return cy.get('tbody tr');
  }

  get firstGeneInTable() {
    return cy.get('tbody td').first();
  }

  get geneSearchInput() {
    return cy.get('#gene-search-input');
  }

  get autismGeneSetsButton() {
    return cy.get('#autism_gene_sets-button');
  }

  get autismGeneSetsDropdown() {
    return cy.get('#autism_gene_sets-dropdown');
  }

  get autismGeneSetsCheckUncheckAllButton() {
    return this.autismGeneSetsDropdown.find('#check-uncheck-all-button');
  }

  get autismGeneSetsDropdownSearch() {
    return this.autismGeneSetsDropdown.find('input[name="search"]');
  }

  get autismGeneSetsDropdownApplyButton() {
    return this.autismGeneSetsDropdown.contains('Apply');
  }

  get allAutismGeneSetsDropdownCheckboxes() {
    return cy.get('gpf-multiple-select-menu#autism_gene_sets-dropdown label input');
  }

  get firstTabCloseButton() {
    return cy.get('nav span').contains('×').first();
  }
}
