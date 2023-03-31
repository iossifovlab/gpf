import { UserManagementPage } from 'cypress/elements/user-management-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe.skip('User management tests', () => {
  const page = new UserManagementPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
    page.loginAdmin();
  });

  beforeEach(() => {
    page.preserveLogin();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.management);
  });

  it.skip('should navigate through all user management tabs', () => {
    page.groupsButton.click();
    page.groupsTable.should('be.visible');

    page.datasetsButton.click();
    page.datasetsTable.should('be.visible');
  });

  it('should create and delete user', () => {
    page.createUserButton.click();
    page.emailInputField.should('be.visible');
    page.nameInputField.should('be.visible');
    page.submitUserButton.should('be.visible');
    page.cancelUserButton.should('be.visible');

    page.emailInputField.type('test_email@email.com');
    page.nameInputField.type('test_name');
    page.submitUserButton.click();

    page.emailInputField.should('not.exist');
    page.nameInputField.should('not.exist');
    page.submitUserButton.should('not.exist');
    page.cancelUserButton.should('not.exist');

    page.usersTableCells.should('have.length', 15);
    page.usersTableCells.first().should('have.text', 'test_nametest_email@email.com');
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    page.userActionsDeleteUser('test_email@email.com').click();
    page.userTableDeleteUserConfirmButton.click();

    page.usersTableCells.should('have.length', 10);
  });

  it('should fail to create user with already used email', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.usersTableCells.should('have.length', 15);

    createTestUser(page, 'test_email@email.com', 'test_name');

    page.alertElement.invoke('text').then((text) => text.trim())
      .should('equal', 'Error: wdae user with this email already exists.');
    page.cancelUserButton.click();

    page.usersTableCells.should('have.length', 15);
    page.userCell('test_email@email.com').should('have.text', 'test_nametest_email@email.com');
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    deleteTestUser(page, 'test_email@email.com');
  });

  it('should not be able to create user with no email or name', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.emailInputField.type('test_email@email.com');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.emailInputField.clear();
    page.nameInputField.type('test_name');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.cancelUserButton.click();
  });

  it('should not create user with invalid email or name', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.nameInputField.type('test_name');
    page.emailInputField.type('test_email@email.c');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('test_email@');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('test_email');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('test_email@email');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.nameInputField.clear();
    page.emailInputField.clear();
    page.emailInputField.type('test_email@email.com');

    page.nameInputField.type('te');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.nameInputField.clear();
    page.nameInputField.type('t');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.cancelUserButton.click();
  });

  it('should search and filter users', () => {
    page.userSearchField.type('admin');
    page.usersTableCells.should('have.length', 5);
    page.userSearchField.clear();
    // triggers search event
    page.userSearchField.type(' ');
    page.usersTableCells.should('have.length', 10);
  });

  it('should search and find user', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.userSearchField.type('test_name');
    page.userCell('test_email@email.com').should('have.text', 'test_nametest_email@email.com');
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    page.userSearchField.clear();
    page.userSearchField.type('test_email@email.com');
    page.userCell('test_email@email.com').should('have.text', 'test_nametest_email@email.com');
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');
    deleteTestUser(page, 'test_email@email.com');
  });

  it('should search and do not find user', () => {
    page.userSearchField.type('comp');
    page.usersTableCells.should('not.exist');

    page.userSearchField.clear();
    page.userSearchField.type('test_name');
    page.usersTableCells.should('not.exist');
  });

  it('should edit and delete username', () => {
    createTestUser(page, 'test_email@email.com', 'test_name1');
    page.userCell('test_email@email.com').should('have.text', 'test_name1test_email@email.com');
    page.userCell('test_email@email.com').find('#edit-icon').should('be.visible');
    page.userCell('test_email@email.com').find('#edit-icon').click();

    page.userNameInput('test_email@email.com').should('be.visible');
    page.userNameInput('test_email@email.com').should('have.value', 'test_name1');
    page.userCell('test_email@email.com').find('#cancel-button').should('be.visible');
    page.userCell('test_email@email.com').find('#user-name').should('not.exist');
    page.userCell('test_email@email.com').find('#edit-icon').should('not.exist');

    // edit username
    page.userNameInput('test_email@email.com').clear();
    page.userNameInput('test_email@email.com').type('test_name{enter}');
    page.userCell('test_email@email.com').find('#user-name').should('have.text', 'test_name');

    // delete username
    page.userCell('test_email@email.com').find('#edit-icon').click();
    page.userNameInput('test_email@email.com').clear();
    page.userNameInput('test_email@email.com').type('{enter}');
    page.userNameInput('test_email@email.com').should('be.visible');
    page.userCell('test_email@email.com').find('#cancel-button').click();
    page.userCell('test_email@email.com').find('#user-name').should('have.text', 'test_name');

    deleteTestUser(page, 'test_email@email.com');
  });

  it('should test when cancel editing the username', () => {
    page.userCell('admin@iossifovlab.com').should('have.text', 'Add usernameadmin@iossifovlab.com');
    page.userCell('admin@iossifovlab.com').find('#edit-icon').click();
    page.userNameInput('admin@iossifovlab.com').type('admin');
    page.userCell('admin@iossifovlab.com').find('#cancel-button').click();
    page.userCell('admin@iossifovlab.com').find('#add-user-name').should('have.text', 'Add username');
  });

  it.skip('should add and remove groups', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.usersTableCells.first().should('have.text', 'test_nametest_email@email.com');
    page.userGroupsCell('test_email@email.com').find('.add-button').should('be.visible');

    // add groups
    page.userGroupsCell('test_email@email.com').find('.add-button').click();
    page.groupsMenu.should('be.visible');
    page.groupsMenuSearch.type('comp_all');
    page.findButtonInComponentContainingText('.add-item-button', 'comp_all').click();
    page.userDatasetsCell('test_email@email.com').should('have.text', 'comp_all');

    page.groupsMenuSearchClear.click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.userGroupList('test_email@email.com').should('have.text', 'iossifov_2014comp_allany_usertest_email@email.com');
    page.userDatasetsCell('test_email@email.com').should('have.text', 'iossifov_2014comp_all');


    //remove groups
    page.userGroupList('test_email@email.com').find('#comp_all-list-item #confirm-button').click();
    page.userTableRemoveGroupConfirm.click();
    page.userGroupList('test_email@email.com').should('have.text', 'iossifov_2014any_usertest_email@email.com');

    page.userGroupList('test_email@email.com').find('#iossifov_2014-list-item #confirm-button').click();
    page.userTableCancelRemoveGroupConfirm.click();
    page.userGroupList('test_email@email.com').should('have.text', 'iossifov_2014any_usertest_email@email.com');

    page.userDatasetsCell('test_email@email.com').should('have.text', 'iossifov_2014');

    page.userGroupList('test_email@email.com').find(
      '#any_user-list-item #confirm-button').should('not.exist');

    // page.userGroupList('test_email@email.com').find(
    //   '#test_email@email.com-list-item #confirm-button').should('not.exist');
    deleteTestUser(page, 'test_email@email.com');
  });

  it('should check admin', () => {
    page.userGroupsCell('admin@iossifovlab.com').find('#admin-list-item #confirm-button').should('not.exist');

    page.userDatasetsCell('admin@iossifovlab.com').should('have.text',
      'comp_vcfiossifov_2014multicomp_denovocomp_allCOMP GenotypesALL Genotypes');

    page.userActionsResetPassword('admin@iossifovlab.com').should('be.visible');
    page.userActionsDeleteUser('admin@iossifovlab.com').should('not.exist');
  });

  // groups ------------------------------------------------------------------------------------------

  it('should create and delete group with user and dataset', () => {
    page.groupsButton.click();

    page.createGroupButton.click();
    page.createGroupNameInput.should('be.visible');
    page.createButton.should('be.visible');
    page.createGroupCancel.should('be.visible');

    page.createGroupNameInput.type('test_group');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    // add user
    page.groupsTableCells.first().should('have.text',
      'test_groupEmpty groups with no users or datasets will be deleted!');
    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('research@iossifovlab.com');
    page.findButtonInComponentContainingText('.add-item-button', 'research@iossifovlab.com').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group').should('have.text', 'research@iossifovlab.com');

    // add dataset
    page.groupDatasetsCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.groupDatasetsList('test_group').should('have.text', 'iossifov_2014');

    // check if the group is added
    page.datasetsButton.click();
    page.groupsButton.click();
    page.groupsTableCells.should('have.length', 40);
    page.groupCell('test_group').should('exist');

    // delete the group
    page.groupsButton.click();
    page.groupActionsDeleteGroup('test_group').click();
    page.removeGroupConfirmButton.click();
    page.groupsTableCells.should('have.length', 36);
  });

  it('should create and delete group with user only', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group');

    // add user
    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group').should('have.text', 'test_email@email.com');

    // check if the group is added
    page.datasetsButton.click();
    page.groupsButton.click();
    page.groupCell('test_group').should('exist');

    deleteTestGroup(page, 'test_group');
  });

  it('should create and delete group with dataset only', () => {
    createTestGroup(page, 'test_group');

    // add dataset
    page.groupDatasetsCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupDatasetsList('test_group').should('have.text', 'iossifov_2014');

    // check if the group is added
    page.datasetsButton.click();
    page.groupsButton.click();
    page.groupCell('test_group').should('exist');

    deleteTestGroup(page, 'test_group');
  });

  it('should create group with no users or datasets', () => {
    page.groupsButton.click();

    page.createGroupButton.click();

    page.createGroupNameInput.type('test_group');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    page.datasetsButton.click();
    page.groupsButton.click();
    page.groupCell('test_group').should('not.exist');
  });

  it.skip('should add and remove user from group', () => {
    createTestGroup(page, 'test_group');
    createTestUser(page, 'test_email@email.com', 'test_name');

    // check for error message
    page.getUserEditorButtonByEmail('test_email@email.com').click();
    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowGroupDropdownListCheckboxes.last().click();
    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowSubmitButton.click();
    page.usersTableCells.last().should(
      'have.text',
      'test_nametest_email@email.comany_usertest_email@email.comtest_group×multi'
    );

    page.groupsButton.click();
    page.groupsTableCells.last().should('contain.text', 'test_email@email.com');

    page.usersButton.click();
    page.userTableRemoveUserGroupButton.click();
    page.userTableRemoveUserGroupConfirmButton.click();
    waitForRequest('GET', '/gpf/api/v3/users/streaming_search?search=', 'usersUpdate', 200);
    page.usersTableCells.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    // deleteTestGroup(page);
    // deleteTestUser(page);
  });

  it('should check if the new groups are in Users', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group1');
    page.groupUsersCell('test_group1').find('.add-button').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    createTestGroup(page, 'test_group2');
    page.groupDatasetsCell('test_group2').find('.add-button').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();

    // check of the group is in user's group list
    page.usersButton.click();
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.comtest_group1');

    // add group to user's group list
    page.userGroupsCell('test_email@email.com').find('.add-button').click();
    page.groupsMenuSearch.type('test_group2');
    page.findButtonInComponentContainingText('.add-item-button', 'test_group2').click();
    page.userGroupList('test_email@email.com').should('have.text',
      'any_usertest_email@email.comtest_group1test_group2');

    // check the users list of the test_group2
    page.groupsButton.click();
    page.groupUsersList('test_group2').should('have.text', 'test_email@email.com');

    // delete groups
    deleteTestGroup(page, 'test_group1');
    deleteTestGroup(page, 'test_group2');

    // check if the groups are not in the list
    page.usersButton.click();
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    deleteTestUser(page, 'test_email@email.com');
  });

  it('should check if the new group is deleted after removing it in Users', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group');
    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    // remove the group from user's group list
    page.usersButton.click();
    page.userGroupList('test_email@email.com').find('#test_group-list-item #confirm-button').click();
    page.userTableRemoveGroupConfirm.click();
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    // check if the group is deleted in Groups
    page.groupsButton.click();
    page.groupUsersList('test_group').should('not.exist');

    page.usersButton.click();
    deleteTestUser(page, 'test_email@email.com');
  });

  it('should check if the new group is deleted after deleting the user', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group');
    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    // delete user
    page.usersButton.click();
    deleteTestUser(page, 'test_email@email.com');

    // check if the group is deleted in Groups
    page.groupsButton.click();
    page.groupUsersList('test_group').should('not.exist');
  });

  it.skip('should give dataset access to user', () => {
    createTestGroup(page, 'test_group');
    createTestUser(page, 'test_email@email.com', 'test_name');

    page.getUserEditorButtonByEmail('test_email@email.com').click();

    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowGroupDropdownListCheckboxes.last().click();
    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowSubmitButton.click();

    page.datasetsButton.click();
    page.datasetsTableRows.last().should('contain.text', 'test_email@email.com');

    page.usersButton.click();
    page.userTableRemoveUserGroupButton.click();
    page.userTableRemoveUserGroupConfirmButton.click();
    waitForRequest('GET', '/gpf/api/v3/users/streaming_search?search=**', 'usersUpdate', 200);
    page.datasetsButton.click();
    page.datasetsTableRows.last().should('not.contain.text', 'test_email@email.com');

    // deleteTestGroup(page);
    // deleteTestUser(page);
  });
});

function createTestUser(page: UserManagementPage, email: string, name: string): void {
  page.usersButton.click();
  page.createUserButton.click();

  page.emailInputField.type(email);
  page.nameInputField.type(name);
  page.submitUserButton.click();
}

function deleteTestUser(page: UserManagementPage, userEmail: string): void {
  page.usersButton.click();
  page.userActionsDeleteUser(userEmail).click();
  page.userTableDeleteUserConfirmButton.click();
}

function createTestGroup(page: UserManagementPage, groupName: string): void {
  page.groupsButton.click();
  page.createGroupButton.click();
  page.createGroupNameInput.type(groupName);
  page.createButton.click();
}

function deleteTestGroup(page: UserManagementPage, groupName: string): void {
  page.groupsButton.click();
  page.groupActionsDeleteGroup(groupName).click();
  page.removeGroupConfirmButton.click();
}

function waitForRequest(method: string, url: string, name: string, response: number): void {
  cy.intercept({method: method, url: url}).as(name);
  cy.wait('@' + name).its('response.statusCode').should('eq', response);
}
