import { BasePage } from './utils';

export class UserManagementPage extends BasePage {
  public get window(): element {
    return cy.get('gpf-management');
  }

  public get usersButton(): element {
    return cy.get('li#users a').contains('Users');
  }

  public get usersTable(): element {
    return cy.get('gpf-users-table');
  }

  public get createUserButton(): element {
    return cy.get('#create-user-form-button');
  }

  public get emailInputField(): element {
    return cy.get('#email-box');
  }

  public get nameInputField(): element {
    return cy.get('#name-box');
  }

  public get submitUserButton(): element {
    return cy.get('#create-user-button');
  }

  public get cancelUserButton(): element {
    return cy.get('#cancel-user-creation-button');
  }

  public get backUserConfirmationButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Back');
  }

  public get alertElement(): element {
    return cy.get('.creation-error');
  }

  public get usersTableCells(): element {
    return cy.get('gpf-users-table .grid-cell');
  }

  public get userTableDeleteNewestUserButton(): element {
    return cy.get('button[title="Delete user"]');
  }

  public get userTableDeleteUserConfirmButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Delete');
  }

  public getUserEditorButtonByEmail(email: string): element {
    return cy.get('gpf-table a').contains(email);
  }

  public get allUserEditGroupRemoveButtons(): element {
    return cy.get('ng-multiselect-dropdown a');
  }

  public get userWindowGroupDropDownMenuButton(): element {
    return cy.get('gpf-user-groups-selector .dropdown-btn');
  }

  public get userWindowGroupDropdownList(): element {
    return cy.get('gpf-user-groups-selector div.dropdown-list');
  }

  public get userWindowGroupDropdownSearch(): element {
    return cy.get('gpf-user-groups-selector input[aria-label=\'multiselect-search\']');
  }

  public get userWindowGroupDropdownListCheckboxes(): element {
    return cy.get('gpf-user-groups-selector ul.item2 li');
  }

  public get userWindowSubmitButton(): element {
    return cy.get('button').contains('Submit');
  }

  public get userTableRemoveUserGroupButton(): element {
    return cy.get('gpf-users-table button[title=\'Remove group\']').last();
  }

  public get userTableRemoveUserGroupConfirmButton(): element {
    return cy.get('gpf-users-table mwl-confirmation-popover-window button').contains('Remove group');
  }

  public get userSearchField(): element {
    return cy.get('gpf-user-management input#search-field');
  }

  public get groupsButton(): element {
    return cy.get('li#groups a').contains('Groups');
  }

  public get groupsTable(): element {
    return cy.get('gpf-groups-table');
  }

  public get groupsTableRows(): element {
    return cy.get('gpf-groups-table .table-row');
  }

  public get datasetsButton(): element {
    return cy.get('li#datasets a').contains('Datasets');
  }

  public get datasetsTable(): element {
    return cy.get('gpf-datasets-table');
  }

  public get datasetsTableRows(): element {
    return cy.get('gpf-datasets-table .table-row');
  }

  public get datasetsTableAddGroupToLastDatasetInputField(): element {
    return cy.get('gpf-datasets-table input.form-control').last();
  }

  public get datasetsTableAddGroupToLastDatasetButton(): element {
    return cy.get('gpf-datasets-table button').filter(':contains(\'Add\')').last();
  }

  public get datasetsTableRemoveNewestGroupInLastDatasetButton(): element {
    return cy.get('gpf-datasets-table button[title=\'Remove group\']').last();
  }

  public get datasetsTableRemoveGroupConfirmButton(): element {
    return cy.get('gpf-datasets-table mwl-confirmation-popover-window button').contains('Remove group');
  }
}
