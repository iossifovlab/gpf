import { BasePage } from './utils';

export class PhenoBrowserPage extends BasePage {
  get window() {
    return cy.get('gpf-pheno-browser');
  }

  get searchInputBox() {
    return cy.get('input.form-control');
  }

  get allTableRows() {
    return cy.get('gpf-table > div > div.ng-star-inserted');
  }

  get tableDiv() {
    return cy.get('.col-lg-12');
  }

  get instrumentsBox() {
    return cy.get('select.form-control');
  }

  get headerCells() {
    return this.tableDiv.get('gpf-table-view-header-cell');
  }

  get tableCells() {
    return this.tableDiv.get('gpf-table-view-cell');
  }

  get tableRows() {
    return this.tableDiv.get('gpf-pheno-browser-table > gpf-table > div > div.ng-star-inserted');
  }

  get downloadButton() {
    return cy.get('.col-4 > a');
  }
}
