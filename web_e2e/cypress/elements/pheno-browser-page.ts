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
}
