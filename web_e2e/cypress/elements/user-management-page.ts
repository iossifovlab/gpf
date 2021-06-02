import { BasePage } from './utils';

export class UserManagementPage extends BasePage {
  get window() {
    return cy.get('gpf-management');
  }

  get usersButton() {
    return cy.get('li#users a').contains('Users');
  }

  get usersTable() {
    return cy.get('gpf-users-table');
  }

  get usersCreateWindow() {
    return cy.get('gpf-users-create');
  }

  get createUserButton() {
    return cy.get('gpf-user-management a').contains('Create user');
  }

  get emailInputField() {
    return cy.get('gpf-users-create input#email');
  }

  get nameInputField() {
    return cy.get('gpf-users-create input#name');
  }

  get submitUserButton() {
    return cy.get('gpf-users-create button').contains('Submit');
  }

  get backUserButton() {
    return cy.get('gpf-users-create button').contains('Back');
  }

  get backUserConfirmationButton() {
    return cy.get('mwl-confirmation-popover-window button').contains('Back');
  }

  get alertElement() {
    return cy.get('gpf-users-create div.alert.alert-danger');
  }

  get usersTableRows() {
    return cy.get('gpf-users-table gpf-table > div > div[class=\'ng-star-inserted\']');
  }

  get userTableEmailElements() {
    return cy.get('gpf-table-view-cell a[href*=\'/gpf/management/users/\']');
  }

  get userTableDeleteNewestUserButton() {
    return cy.get('gpf-users-actions a').last();
  }

  get userTableDeleteUserConfirmButton() {
    return cy.get('mwl-confirmation-popover-window button').contains('Delete');
  }

  getUserEditorButtonByEmail(email: string) {
    return cy.get('gpf-table a').contains(email);
  }

  get allUserEditGroupRemoveButtons() {
    return cy.get('ng-multiselect-dropdown a');
  }

  get userEditWindow() {
    return cy.get('gpf-user-edit');
  }

  get groupsBulkAddWindow() {
    return cy.get('gpf-groups-bulk-add');
  }

  get groupsBulkRemoveWindow() {
    return cy.get('gpf-groups-bulk-remove');
  }

  get userWindowGroupDropDownMenuButton() {
    return cy.get('gpf-user-groups-selector .dropdown-btn');
  }

  get userWindowGroupDropdownList() {
    return cy.get('gpf-user-groups-selector div.dropdown-list');
  }

  get userWindowGroupDropdownSearch() {
    return cy.get('gpf-user-groups-selector input[aria-label=\'multiselect-search\']');
  }

  get userWindowGroupDropdownListCheckboxes() {
    return cy.get('gpf-user-groups-selector ul.item2 li');
  }

  get userWindowSubmitButton() {
    return cy.get('button').contains('Submit');
  }

  get userTableRemoveUserGroupButton() {
    return cy.get('gpf-users-table button[title=\'Remove group\']').last();
  }

  get userTableRemoveUserGroupConfirmButton() {
    return cy.get('gpf-users-table mwl-confirmation-popover-window button').contains('Remove group');
  }

  get userBulkEditButton() {
    return cy.get('gpf-user-management button#btnGroupDrop1');
  }

  get userBulkEditAddGroupButton() {
    return cy.get('gpf-user-management button').contains('Add group');
  }

  get userBulkEditRemoveGroupButton() {
    return cy.get('gpf-user-management button').contains('Remove group');
  }

  get userSearchField() {
    return cy.get('gpf-user-management input#search-field');
  }

  get usersEditorAddGroupButton() {
    return cy.get('gpf-groups-bulk-add button').contains('Add Group');
  }

  get usersEditorRemoveGroupButton() {
    return cy.get('gpf-groups-bulk-remove button').contains('Remove Group');
  }

  get groupsButton() {
    return cy.get('li#groups a').contains('Groups');
  }

  get groupsTable() {
    return cy.get('gpf-groups-table');
  }

  get groupsTableRows() {
    return cy.get('gpf-groups-table gpf-table > div > div[class=\'ng-star-inserted\']');
  }

  get datasetsButton() {
    return cy.get('li#datasets a').contains('Datasets');
  }

  get datasetsTable() {
    return cy.get('gpf-datasets-table');
  }

  get datasetsTableRows() {
    return cy.get('gpf-datasets-table gpf-table > div > div[class=\'ng-star-inserted\']');
  }

  get datasetsTableAddGroupToLastDatasetInputField() {
    return cy.get('gpf-datasets-table input.form-control').last();
  }

  get datasetsTableAddGroupToLastDatasetButton() {
    return cy.get('gpf-datasets-table button').filter(':contains(\'Add\')').last();
  }

  get datasetsTableRemoveNewestGroupInLastDatasetButton() {
    return cy.get('gpf-datasets-table button[title=\'Remove group\']').last();
  }

  get datasetsTableRemoveGroupConfirmButton() {
    return cy.get('gpf-datasets-table mwl-confirmation-popover-window button').contains('Remove group');
  }
}
