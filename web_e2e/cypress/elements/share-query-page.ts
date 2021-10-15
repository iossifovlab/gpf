import { BasePage } from './utils';

export class ShareQueryPage extends BasePage {
  get button() {
    return cy.get('#share-query-dropdown-button');
  }

  get dropdownMenu() {
    return cy.get('#share-query-dropdown');
  }

  get input() {
    return cy.get('div#share-query-dropdown input');
  }
}
