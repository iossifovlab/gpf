import { BasePage } from './utils';

export class SavedQueriesPage extends BasePage {
  public get tableFirstLoadButton(): element {
    return cy.get('gpf-table-view-cell a').contains('Load').first();
  }

  public get tableFirstDeleteButton(): element {
    return cy.get('gpf-table-view-cell button').contains('Delete').first();
  }
}
