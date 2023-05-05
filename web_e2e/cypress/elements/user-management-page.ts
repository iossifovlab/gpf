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

  public userCell(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-user-cell"]`);
  }

  public userNameInput(userEmail: string): element {
    return cy.get(`input[id="${userEmail}-new-name-input"]`);
  }

  public userGroupList(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-groups-list"]`);
  }

  public userGroupListItem(email: string, group: string): element {
    return this.userGroupList(email).find(`div[id="${group}-list-item"]`);
  }

  public userAddGroupButton(email: string): element {
    return this.userGroupsCell(email).find('.add-button');
  }

  public userGroupRemoveButton(email: string, group: string): element {
    return this.userGroupList(email).find(`div[id="${group}-list-item"] #confirm-button`);
  }

  public userHasPasswordCell(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-password-cell"]`);
  }

  public userGroupsCell(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-groups-cell"]`);
  }

  public userDatasetsCell(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-datasets-cell"]`);
  }

  public userActionsCell(userEmail: string): element {
    return cy.get(`div[id="${userEmail}-actions-cell"]`);
  }

  public userActionsResetPassword(userEmail: string): element {
    return cy.get(`gpf-confirm-button[id="${userEmail}-reset-password-button"]`);
  }

  public userActionsDeleteUser(userEmail: string): element {
    return cy.get(`gpf-confirm-button[id="${userEmail}-delete-user-button"]`);
  }

  public get submitUserButton(): element {
    return cy.get('#create-user-button');
  }

  public get cancelUserCreationButton(): element {
    return cy.get('#cancel-user-creation-button');
  }

  public get backUserConfirmationButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Back');
  }

  public get alertElement(): element {
    return cy.get('.creation-error');
  }

  public get menu(): element {
    return cy.get('#menu');
  }

  public menuSearch(text: string): void {
    cy.get('.search-input-wrapper > input').type(text);
  }

  public get menuSearchClear(): element {
    return cy.get('.search-clear-icon');
  }

  public get userRemoveGroupConfirm(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Remove');
  }

  public get userCancelRemoveGroupConfirm(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Cancel');
  }

  public get usersTableCells(): element {
    return cy.get('gpf-users-table .grid-cell');
  }

  public get userTableDeleteUserConfirmButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Delete');
  }

  public get userTableResetPasswordConfirmButton(): element {
    return cy.get('mwl-confirmation-popover-window button').contains('Reset');
  }

  public get newPasswordInput(): element {
    return cy.get('#id_new_password1');
  }

  public get repeatNewPasswordInput(): element {
    return cy.get('#id_new_password2');
  }

  public get newPasswordButton(): element {
    return cy.get('input[value="Reset password"]');
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

  public get groupsTableCells(): element {
    return cy.get('gpf-groups-table .grid-cell');
  }

  public get createGroupButton(): element {
    return cy.get('#create-group-form-button');
  }

  public get createGroupNameInput(): element {
    return cy.get('#group-name-box');
  }

  public get createButton(): element {
    return cy.get('#create-group-button');
  }

  public get cancelGroupCreationButton(): element {
    return cy.get('#cancel-group-creation-button');
  }

  public get searchGroup(): element {
    return cy.get('#search-field');
  }

  public groupCell(group: string): element {
    return cy.get(`div[id="${group}-group-cell"]`);
  }

  public groupUsersCell(group: string): element {
    return cy.get(`div[id="${group}-users-cell"]`);
  }

  public groupUsersList(group: string): element {
    return cy.get(`div[id="${group}-users-list"]`);
  }

  public groupUsersListItem(group: string, email: string): element {
    return this.groupUsersList(group).find(`div[id="${email}-list-item"]`);
  }

  public groupRemoveUserButton(group: string, email: string): element {
    return this.groupUsersList(group).find(`div[id="${email}-list-item"] #confirm-button`);
  }

  public groupAddUserButton(group: string): element {
    return this.groupUsersCell(group).find('.add-button');
  }

  public groupDatasetsCell(group: string): element {
    return cy.get(`div[id="${group}-datasets-cell"]`);
  }

  public groupDatasetsList(group: string): element {
    return cy.get(`div[id="${group}-datasets-list"]`);
  }

  public groupDatasetsListItem(group: string, dataset: string): element {
    return this.groupDatasetsList(group).find(`div[id="${dataset}-list-item"]`);
  }

  public groupAddDatasetButton(group: string): element {
    return this.groupDatasetsCell(group).find('.add-button');
  }

  public groupRemoveDatasetButton(group: string, dataset: string): element {
    return this.groupDatasetsList(group).find(`div[id="${dataset}-list-item"] #confirm-button`);
  }

  public get removeDatasetOrUserConfirmButton(): element {
    return cy.get('gpf-groups-table mwl-confirmation-popover-window button').contains('Remove');
  }

  public groupActionsCell(group: string): element {
    return cy.get(`div[id="${group}-actions-cell"]`);
  }

  public get groupsWarningMessage(): element {
    return cy.get('#group-deletion-warning');
  }

  public groupActionsDeleteGroup(group: string): element {
    return cy.get(`gpf-confirm-button[id="${group}-delete-group-button"]`);
  }

  public get deleteGroupConfirmButton(): element {
    return cy.get('gpf-groups-table mwl-confirmation-popover-window button').contains('Delete');
  }

  public get datasetsButton(): element {
    return cy.get('li#datasets a').contains('Datasets');
  }

  public get datasetsTable(): element {
    return cy.get('gpf-datasets-table');
  }

  public datasetCell(dataset: string): element {
    return cy.get(`div[id="${dataset}-dataset-cell"]`);
  }

  public datasetGroupCell(dataset: string): element {
    return cy.get(`div[id="${dataset}-groups-cell"]`);
  }

  public datasetGroupList(dataset: string): element {
    return cy.get(`div[id="${dataset}-groups-list"]`);
  }

  public datasetGroupListItem(dataset: string, group: string): element {
    return this.datasetGroupList(dataset).find(`div[id="${group}-list-item"]`);
  }

  public datasetGroupRemoveButton(dataset: string, group: string): element {
    return this.datasetGroupList(dataset).find(`div[id="${group}-list-item"] #confirm-button`);
  }

  public datasetAddGroupButton(dataset: string): element {
    return this.datasetGroupCell(dataset).find('.add-button');
  }

  public datasetUserCell(dataset: string): element {
    return cy.get(`div[id="${dataset}-users-cell"]`);
  }

  public datasetUserList(dataset: string): element {
    return cy.get(`div[id="${dataset}-users-list-cell"]`);
  }

  public datasetUserListItem(dataset: string, email: string): element {
    return this.datasetUserList(dataset).find(`div[id="${email}-list-item"]`);
  }

  public get datasetsRemoveGroupConfirmButton(): element {
    return cy.get('gpf-datasets-table mwl-confirmation-popover-window button').contains('Remove');
  }
}
