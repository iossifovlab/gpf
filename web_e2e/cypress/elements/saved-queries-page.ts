import { BasePage } from './utils';

export class SavedQueriesPage extends BasePage {
  public queryNameCell(tableName: string, queryName: string): element {
    return cy.get(`div[id="${tableName}-table"]`).find(`div[id="query-${queryName}-name-cell"]`);
  }

  public queryDescriptionCell(tableName: string, queryName: string): element {
    return cy.get(`div[id="${tableName}-table"]`).find(`div[id="query-${queryName}-description-cell"]`);
  }

  public queryActionsCell(tableName: string, queryName: string): element {
    return cy.get(`div[id="${tableName}-table"]`).find(`div[id="query-${queryName}-actions-cell"]`);
  }

  public queryLoadButton(tableName: string, queryName: string): element {
    return this.queryActionsCell(tableName, queryName).find('#load-button');
  }

  public queryCopyLinkButton(tableName: string, queryName: string): element {
    return this.queryActionsCell(tableName, queryName).find('#copy-link-button');
  }

  public queryDeleteButton(tableName: string, queryName: string): element {
    return this.queryActionsCell(tableName, queryName).find('#delete-button');
  }
}
