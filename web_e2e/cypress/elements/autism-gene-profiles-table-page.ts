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

  get firstGeneLink() {
    return cy.get('tbody td').first();
  }

  get firstTabCloseButton() {
    return cy.get('nav span').contains('×').first();
  }
}
