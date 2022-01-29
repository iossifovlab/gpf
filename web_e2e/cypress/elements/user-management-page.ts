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
    return cy.get('gpf-user-management a').contains('Create user');
  }

  public get emailInputField(): element {
    return cy.get('gpf-users-create input#email');
  }

  public get nameInputField(): element {
    return cy.get('gpf-users-create input#name');
  }

  public get submitUserButton(): element {
    return cy.get('gpf-users-create button').contains('Submit');
  }

  public get backUserButton(): element {
    return cy.get('gpf-users-create button').contains('Back');
  }

  public get backUserConfirmationButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Back');
  }

  public get alertElement(): element {
    return cy.get('gpf-users-create div.alert.alert-danger');
  }

  public get usersTableRows(): element {
    return cy.get('gpf-users-table gpf-table > div > div[class=\'ng-star-inserted\']');
  }

  public get userTableDeleteNewestUserButton(): element {
    return cy.get('gpf-users-actions a').last();
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
    return cy.get('gpf-groups-table gpf-table > div > div[class=\'ng-star-inserted\']');
  }

  public get datasetsButton(): element {
    return cy.get('li#datasets a').contains('Datasets');
  }

  public get datasetsTable(): element {
    return cy.get('gpf-datasets-table');
  }

  public get datasetsTableRows(): element {
    return cy.get('gpf-datasets-table gpf-table > div > div[class=\'ng-star-inserted\']');
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
