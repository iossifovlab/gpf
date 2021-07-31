import { BasePage } from './utils';

export class AutismGeneProfilesTable extends BasePage {
  get window() {
    return cy.get('gpf-autism-gene-profiles-table');
  }

  get table() {
    return cy.get('gpf-autism-gene-profiles-table table');
  }

  get allTableCells() {
    return this.table.find('tbody td');
  }

  get allTableRows() {
    return this.table.find('tbody tr');
  }

  get firstGeneInTable() {
    return this.allTableCells.first();
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
    return this.autismGeneSetsDropdown.find('label input');
  }

  get firstTabCloseButton() {
    return cy.get('nav span').contains('×').first();
  }
}
