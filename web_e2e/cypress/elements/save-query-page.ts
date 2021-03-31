import { BasePage } from './utils';


export class SaveQueryPage extends BasePage {
  get button() {
    return cy.get('#save-query-dropdown-button');
  }

  get dropdownMenu() {
    return cy.get('#save-query-dropdown');
  }

  get dropdownNameInput() {
    return cy.get('gpf-save-query input#name');
  }

  get saveButton() {
    return cy.get('gpf-save-query form > button');
  }

  get tableFirstLoadButton() {
    return cy.get('gpf-table-view-cell a').contains('Load').first();
  }

  get tableFirstDeleteButton() {
    return cy.get('gpf-table-view-cell button').contains('Delete').first();
  }

  get savedQueriesTableWindow() {
    return cy.get('gpf-saved-queries');
  }

  get errorAlertWindow() {
    return cy.get('gpf-save-query div.alert.alert-danger');
  }
}
