import { BasePage } from './utils';

export class SaveQueryPage extends BasePage {
  public get button(): element {
    return cy.get('#save-query-dropdown-button');
  }

  public get dropdownMenu(): element {
    return cy.get('#save-query-dropdown');
  }

  public get dropdownNameInput(): element {
    return cy.get('gpf-save-query input#name');
  }

  public get saveButton(): element {
    return cy.get('gpf-save-query form > button');
  }

  public get tableFirstLoadButton(): element {
    return cy.get('gpf-table-view-cell a').contains('Load').first();
  }

  public get tableFirstDeleteButton(): element {
    return cy.get('gpf-table-view-cell button').contains('Delete').first();
  }

  public get savedQueriesTableWindow(): element {
    return cy.get('gpf-saved-queries');
  }

  public get errorAlertWindow(): element {
    return cy.get('gpf-save-query div.alert.alert-danger');
  }
}
