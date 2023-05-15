import { UserManagementPage } from 'cypress/elements/user-management-page';
import { UsersPage } from 'cypress/elements/users-page';
import { sidenavPageLinks } from 'cypress/elements/utils';
import 'cypress-if';
import { PedigreeSelectorPage } from 'cypress/elements/pedigree-selector-page';

describe('User management tests for reset password in Users', () => {
  const page = new UserManagementPage();
  const usersPage = new UsersPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
  });

  it('should reset password', () => {
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    createTestUser(page, 'user_reset_password@email.com', 'user_reset_password_name');
    page.userHasPasswordCell('user_reset_password@email.com').should('be.empty');
    page.userActionsResetPassword('user_reset_password@email.com').click();
    page.userTableResetPasswordConfirmButton.click();

    cy.wait(10000);
    cy.request('GET', 'http://mailhog:8025/api/v2/search?kind=to&query=user_reset_password@email.com').then(
      (response: {body: {items: {Content: {Body: string}}[]}}) => {
        const regexUrl = new RegExp(/http(s)?:\/\/[\w_-]+((.[\w_-]))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])/gm, 'i');
        const url = response.body.items[0].Content.Body.match(regexUrl)[0];
        const urlToVisit = url.replace('http://gpf/gpf/', '');
        cy.visit(urlToVisit);
        page.newPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.repeatNewPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.newPasswordButton.click();
      }
    );

    page.logout();
    usersPage.waitLoginAfterLogout();
    page.login('user_reset_password@email.com', 'XC^ZF*TZXuUChFsv');

    page.logout();
    usersPage.waitLoginAfterLogout();
    page.loginAdmin();

    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    page.userHasPasswordCell('user_reset_password@email.com').find('.fa.fa-check').should('be.visible');
    deleteTestUser(page, 'user_reset_password@email.com');
    page.logout();
    usersPage.waitLoginAfterLogout();
  });

  it('should reset password when login', () => {
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    createTestUser(page, 'forgotten_password@email.com', 'forgotten_password_name');
    page.logout();

    cy.window().then((win) => {
      cy.stub(win, 'open', (url: string) => {
        win.location.href = `${Cypress.config().baseUrl}accounts/login/?next=/gpf/o/authorize/%3F${url}`;
      }).as('popup');
    });

    usersPage.waitLoginAfterLogout();
    usersPage.logInButton.click();

    cy.get('@popup').url().then(() => {
      cy.get('a').first().click();
      cy.get('#id_email').type('forgotten_password@email.com');
      cy.get('input[value="Reset password"]').click();
    });

    cy.wait(10000);
    cy.request('GET', 'http://mailhog:8025/api/v2/search?kind=to&query=forgotten_password@email.com').then(
      (response: {body: {items: {Content: {Body: string}}[]}}) => {
        const regexUrl = new RegExp(/http(s)?:\/\/[\w_-]+((.[\w_-]))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])/gm, 'i');
        const url = response.body.items[0].Content.Body.match(regexUrl)[0];
        const urlToVisit = url.replace('http://gpf/gpf/', '');
        cy.visit(urlToVisit);
        page.newPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.repeatNewPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.newPasswordButton.click();
      }
    );

    usersPage.waitLoginAfterLogout();
    page.login('forgotten_password@email.com', 'XC^ZF*TZXuUChFsv');
    page.logout();

    usersPage.waitLoginAfterLogout();
    page.loginAdmin();

    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    deleteTestUser(page, 'forgotten_password@email.com');
    page.logout();
    usersPage.waitLoginAfterLogout();
  });
});

describe('User management tests for Users', () => {
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

  it('should navigate through all user management tabs', () => {
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
    page.cancelUserCreationButton.should('be.visible');

    page.emailInputField.type('test_email@email.com');
    page.nameInputField.type('test_name');
    page.submitUserButton.click();

    page.emailInputField.should('not.exist');
    page.nameInputField.should('not.exist');
    page.submitUserButton.should('not.exist');
    page.cancelUserCreationButton.should('not.exist');

    page.userCell('test_email@email.com').should('exist');
    page.usersTableCells.first().should('have.text', 'test_nametest_email@email.com');
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.com');

    page.userActionsDeleteUser('test_email@email.com').click();
    page.userTableDeleteUserConfirmButton.click();

    page.userCell('test_email@email.com').should('not.exist');
  });

  it('should fail to create user with already used email', () => {
    createTestUser(page, 'used_email@email.com', 'used_name');

    page.createUserButton.click();
    page.emailInputField.type('used_email@email.com');
    page.nameInputField.type('used_name');
    page.submitUserButton.click();

    page.alertElement.invoke('text').then((text) => text.trim())
      .should('equal', 'Error: wdae user with this email already exists.');
    page.cancelUserCreationButton.click();

    page.userCell('used_email@email.com').should('exist');
    page.userCell('used_email@email.com').should('have.text', 'used_nameused_email@email.com');
    page.userGroupList('used_email@email.com').should('have.text', 'any_userused_email@email.com');

    deleteTestUser(page, 'used_email@email.com');
  });

  it('should not be able to create user with no email or name', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.emailInputField.type('no_username_email@email.com');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.emailInputField.clear();
    page.nameInputField.type('no_email_name');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.cancelUserCreationButton.click();
    page.userCell('no_username_email@email.com').should('not.exist');
  });

  it('should not create user with invalid email or name', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.nameInputField.type('valid_test_name');
    page.emailInputField.type('invalid_email@email.c');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('invalid_email@');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('invalid_email');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.clear();
    page.emailInputField.type('invalid_email@email');
    page.submitUserButton.click();
    page.emailInputField.should('be.focused');

    page.nameInputField.clear();
    page.emailInputField.clear();
    page.emailInputField.type('valid_email@email.com');

    page.nameInputField.type('te');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.nameInputField.clear();
    page.nameInputField.type('t');
    page.submitUserButton.click();
    page.nameInputField.should('be.focused');

    page.cancelUserCreationButton.click();
  });

  it('should search and find user', () => {
    createTestUser(page, 'search_and_find_email@email.com', 'search_and_find_name');
    page.userSearchField.type('search_and_find_name');
    page.userCell('search_and_find_email@email.com').should(
      'have.text', 'search_and_find_namesearch_and_find_email@email.com'
    );
    page.userGroupList('search_and_find_email@email.com').should(
      'have.text', 'any_usersearch_and_find_email@email.com'
    );

    page.userSearchField.clear();
    page.userSearchField.type('search_and_find_email@email.com');
    page.userCell('search_and_find_email@email.com').should(
      'have.text', 'search_and_find_namesearch_and_find_email@email.com'
    );
    page.userGroupList('search_and_find_email@email.com').should(
      'have.text', 'any_usersearch_and_find_email@email.com'
    );

    page.userSearchField.clear();
    page.userSearchField.type('admin');
    // 5 cells are 1 row
    page.usersTableCells.should('have.length', 5);
    page.userSearchField.clear();

    deleteTestUser(page, 'search_and_find_email@email.com');
  });

  it('should search and not find user', () => {
    page.userSearchField.type('comp');
    page.usersTableCells.should('not.exist');

    page.userSearchField.clear();
    page.userSearchField.type('nonexistent_user_name');
    page.usersTableCells.should('not.exist');
  });

  it('should edit and delete username', () => {
    createTestUser(page, 'edit_username_email@email.com', 'user_name1');
    page.userCell('edit_username_email@email.com').should('have.text', 'user_name1edit_username_email@email.com');
    page.userCell('edit_username_email@email.com').find('#edit-icon').should('be.visible');
    page.userCell('edit_username_email@email.com').find('#edit-icon').click();

    page.userNameInput('edit_username_email@email.com').should('be.visible');
    page.userNameInput('edit_username_email@email.com').should('have.value', 'user_name1');
    page.userCell('edit_username_email@email.com').find('#cancel-button').should('be.visible');
    page.userCell('edit_username_email@email.com').find('#user-name').should('not.exist');
    page.userCell('edit_username_email@email.com').find('#edit-icon').should('not.exist');

    // edit username
    page.userNameInput('edit_username_email@email.com').clear();
    page.userNameInput('edit_username_email@email.com').type('user_name{enter}');
    page.userCell('edit_username_email@email.com').find('#user-name').should('have.text', 'user_name');

    // delete username
    page.userCell('edit_username_email@email.com').find('#edit-icon').click();
    page.userNameInput('edit_username_email@email.com').clear();
    page.userNameInput('edit_username_email@email.com').type('{enter}');
    page.userNameInput('edit_username_email@email.com').should('be.visible');
    page.userCell('edit_username_email@email.com').find('#cancel-button').click();
    page.userCell('edit_username_email@email.com').find('#user-name').should('have.text', 'user_name');

    deleteTestUser(page, 'edit_username_email@email.com');
  });

  it('should test when cancel editing the username', () => {
    page.userCell('admin@iossifovlab.com').should('have.text', 'Add usernameadmin@iossifovlab.com');
    page.userCell('admin@iossifovlab.com').find('#edit-icon').click();
    page.userNameInput('admin@iossifovlab.com').type('admin');
    page.userCell('admin@iossifovlab.com').find('#cancel-button').click();
    page.userCell('admin@iossifovlab.com').find('#add-user-name').should('have.text', 'Add username');
  });

  it('should cancel the process of creating user', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.nameInputField.type('cancel_creation_name');
    page.emailInputField.type('cancel_creation_email@email.com');
    page.cancelUserCreationButton.click();

    page.userCell('cancel_creation_email@email.com').should('not.exist');
  });

  it('should add and remove groups', () => {
    createTestUser(page, 'add_remove_groups_email@email.com', 'add_remove_groups_name');
    page.userAddGroupButton('add_remove_groups_email@email.com').should('be.visible');

    // add groups
    page.userAddGroup('add_remove_groups_email@email.com', 'comp_all');
    page.userDatasetsCell('add_remove_groups_email@email.com').contains('comp_all');
    page.userAddGroup('add_remove_groups_email@email.com', 'iossifov_2014');

    page.userGroupList('add_remove_groups_email@email.com').contains('iossifov_2014');
    page.userGroupList('add_remove_groups_email@email.com').contains('comp_all');
    page.userGroupList('add_remove_groups_email@email.com').contains('any_user');
    page.userGroupList('add_remove_groups_email@email.com').contains('add_remove_groups_email@email.com');
    page.userDatasetsCell('add_remove_groups_email@email.com').contains('iossifov_2014');
    page.userDatasetsCell('add_remove_groups_email@email.com').contains('comp_all');

    //remove groups
    page.userGroupRemoveButton('add_remove_groups_email@email.com', 'comp_all').click();
    page.userRemoveGroupConfirm.click();
    page.userGroupList('add_remove_groups_email@email.com').contains('iossifov_2014');
    page.userGroupList('add_remove_groups_email@email.com').contains('any_user');
    page.userGroupList('add_remove_groups_email@email.com').contains('add_remove_groups_email@email.com');
    page.userGroupList('add_remove_groups_email@email.com').should('not.contain', 'comp_all');

    page.userGroupRemoveButton('add_remove_groups_email@email.com', 'iossifov_2014').click();
    page.userCancelRemoveGroupConfirm.click();
    page.userGroupList('add_remove_groups_email@email.com').contains('iossifov_2014');
    page.userGroupList('add_remove_groups_email@email.com').contains('any_user');
    page.userGroupList('add_remove_groups_email@email.com').contains('add_remove_groups_email@email.com');

    page.userDatasetsCell('add_remove_groups_email@email.com').contains('iossifov_2014');
    page.userDatasetsCell('add_remove_groups_email@email.com').should('not.contain', 'comp_all');

    page.userGroupRemoveButton('add_remove_groups_email@email.com', 'any_user').should('not.exist');
    page.userGroupRemoveButton(
      'add_remove_groups_email@email.com', '#add_remove_groups_email@email.com'
    ).should('not.exist');
    deleteTestUser(page, 'add_remove_groups_email@email.com');
  });

  it('should check admin', () => {
    page.userGroupsCell('admin@iossifovlab.com').find('#admin-list-item #confirm-button').should('not.exist');

    page.userDatasetsCell('admin@iossifovlab.com').should('have.text',
      'comp_vcfiossifov_2014multicomp_denovocomp_allCOMP GenotypesALL Genotypes');

    page.userActionsResetPassword('admin@iossifovlab.com').should('be.visible');
    page.userActionsDeleteUser('admin@iossifovlab.com').should('not.exist');
  });

  it('should create and delete group with user and dataset', () => {
    page.groupsButton.click();

    page.createGroupButton.click();
    page.createGroupNameInput.should('be.visible');
    page.createButton.should('be.visible');
    page.cancelGroupCreationButton.should('be.visible');

    page.createGroupNameInput.type('test_group_with_dataset_user');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    // add user
    page.groupsTableCells.first().should('have.text',
      'test_group_with_dataset_userEmpty groups with no users or datasets will be deleted!');
    page.groupAddUser('test_group_with_dataset_user', 'research@iossifovlab.com');
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group_with_dataset_user').should('have.text', 'research@iossifovlab.com');

    // add dataset
    page.groupAddDataset('test_group_with_dataset_user', 'iossifov_2014');
    page.groupDatasetsList('test_group_with_dataset_user').should('have.text', 'iossifov_2014');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group_with_dataset_user').should('exist');

    // delete the group
    page.groupsButton.click();
    page.groupActionsDeleteGroup('test_group_with_dataset_user').click();
    page.deleteGroupConfirmButton.click();
  });

  it('should create and delete group with user only', () => {
    createTestUser(page, 'group_user_email@email.com', 'group_user_name');
    createTestGroup(page, 'test_group_with_user');

    // add user
    page.groupAddUser('test_group_with_user', 'group_user_email@email.com');
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group_with_user').should('have.text', 'group_user_email@email.com');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group_with_user').should('exist');

    deleteTestGroup(page, 'test_group_with_user');
    deleteTestUser(page, 'group_user_email@email.com');
  });

  it('should create and delete group with dataset only', () => {
    createTestGroup(page, 'test_group_with_dataset');

    // add dataset
    page.groupAddDataset('test_group_with_dataset', 'iossifov_2014');
    page.groupsWarningMessage.should('not.exist');
    page.groupDatasetsList('test_group_with_dataset').should('have.text', 'iossifov_2014');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group_with_dataset').should('exist');

    deleteTestGroup(page, 'test_group_with_dataset');
  });

  it('should not create group with no users or datasets', () => {
    page.groupsButton.click();

    page.createGroupButton.click();

    page.createGroupNameInput.type('nonexistent_group');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    cy.reload();
    page.groupCell('nonexistent_group').should('not.exist');
  });

  it('should not create group with invalid name', () => {
    page.groupsButton.click();
    page.createGroupButton.click();

    page.createGroupNameInput.type('c');
    page.createButton.click();
    page.createGroupNameInput.should('be.focused');

    page.createGroupNameInput.clear();
    page.createGroupNameInput.type('cc');
    page.createButton.click();
    page.createGroupNameInput.should('be.focused');

    page.cancelGroupCreationButton.click();
  });

  it('should cancel the process of creating group', () => {
    page.groupsButton.click();
    page.createGroupButton.click();

    page.createGroupNameInput.type('cancel_creation_group');
    page.cancelGroupCreationButton.click();

    page.groupCell('cancel_creation_group').should('not.exist');
  });

  it('should fail to create group with already used name', () => {
    createTestUser(page, 'used_group_name_user_email@email.com', 'used_group_name_username');
    createTestGroup(page, 'used_group_name');
    page.groupAddUser('used_group_name', 'used_group_name_user_email@email.com');

    createTestGroup(page, 'used_group_name');

    page.alertElement.invoke('text').then((text) => text.trim())
      .should('equal', '\'used_group_name\' already exists choose another name!');
    page.cancelGroupCreationButton.click();

    deleteTestGroup(page, 'used_group_name');
    deleteTestUser(page, 'used_group_name_user_email@email.com');
  });

  it('should add and remove users and datasets from group', () => {
    createTestUser(page, 'add_remove_user_email1@email.com', 'add_remove_username1');
    createTestGroup(page, 'add_remove_in_group');

    page.groupAddUser('add_remove_in_group', 'add_remove_user_email1@email.com');
    page.groupAddDataset('add_remove_in_group', 'iossifov_2014');

    createTestUser(page, 'add_remove_user_email2@email.com', 'add_remove_username2');
    createTestUser(page, 'add_remove_user_email3@email.com', 'add_remove_username3');

    page.groupsButton.click();
    page.groupAddUser('add_remove_in_group', 'add_remove_user_email2@email.com');
    page.groupAddUser('add_remove_in_group', 'add_remove_user_email3@email.com');

    // remove dataset
    page.groupRemoveDatasetButton('add_remove_in_group', 'iossifov_2014').click();
    page.removeDatasetOrUserConfirmButton.click();

    // remove users
    page.groupRemoveUserButton('add_remove_in_group', 'add_remove_user_email1@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();
    page.groupRemoveUserButton('add_remove_in_group', 'add_remove_user_email2@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();
    page.groupRemoveUserButton('add_remove_in_group', 'add_remove_user_email3@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();

    page.groupsWarningMessage.should('be.visible');

    // check if the group is removed
    cy.reload();
    page.groupCell('add_remove_in_group').should('not.exist');

    deleteTestUser(page, 'add_remove_user_email1@email.com');
    deleteTestUser(page, 'add_remove_user_email2@email.com');
    deleteTestUser(page, 'add_remove_user_email3@email.com');
  });

  it('should add and remove groups in Users and users in Groups', () => {
    createTestUser(page, 'groups_and_users_email@email.com', 'groups_and_users_username');
    createTestGroup(page, 'groups_and_users_groupname1');
    page.groupAddUser('groups_and_users_groupname1', 'groups_and_users_email@email.com');

    createTestGroup(page, 'groups_and_users_groupname2');
    page.groupAddDataset('groups_and_users_groupname2', 'iossifov_2014');

    // check of the group is in user's group list
    page.usersButton.click();
    page.userGroupList('groups_and_users_email@email.com').contains('any_user');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_email@email.com');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_groupname1');

    // add group to user's group list
    page.userAddGroup('groups_and_users_email@email.com', 'groups_and_users_groupname2');
    page.userGroupList('groups_and_users_email@email.com').contains('any_user');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_email@email.com');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_groupname1');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_groupname2');

    // check the users list of the groups_and_users_groupname2
    page.groupsButton.click();
    page.groupUsersList('groups_and_users_groupname2').contains('groups_and_users_email@email.com');

    // delete groups
    deleteTestGroup(page, 'groups_and_users_groupname1');
    deleteTestGroup(page, 'groups_and_users_groupname2');

    // check if the groups are not in the list
    page.usersButton.click();
    page.userGroupList('groups_and_users_email@email.com').contains('any_user');
    page.userGroupList('groups_and_users_email@email.com').contains('groups_and_users_email@email.com');

    deleteTestUser(page, 'groups_and_users_email@email.com');
  });

  it('should check if new groups are added in Groups and the new users ' +
  'are in group any_user when creating user', () => {
    createTestUser(page, 'any_user_test_email1@email.com', 'any_user_name1');
    createTestUser(page, 'any_user_test_email2@email.com', 'any_user_name2');
    createTestUser(page, 'any_user_test_email3@email.com', 'any_user_name3');

    page.groupsButton.click();
    page.groupCell('any_user_test_email1@email.com').should('exist');
    page.groupUsersList('any_user_test_email1@email.com').should('have.text', 'any_user_test_email1@email.com');
    page.groupCell('any_user_test_email2@email.com').should('exist');
    page.groupUsersList('any_user_test_email2@email.com').should('have.text', 'any_user_test_email2@email.com');
    page.groupCell('any_user_test_email3@email.com').should('exist');
    page.groupUsersList('any_user_test_email3@email.com').should('have.text', 'any_user_test_email3@email.com');

    page.groupUsersList('any_user').contains('any_user_test_email1@email.com');
    page.groupUsersList('any_user').contains('any_user_test_email2@email.com');
    page.groupUsersList('any_user').contains('any_user_test_email3@email.com');

    deleteTestUser(page, 'any_user_test_email1@email.com');
    deleteTestUser(page, 'any_user_test_email2@email.com');
    deleteTestUser(page, 'any_user_test_email3@email.com');
  });

  it('should check if the new group is deleted after removing it in Users', () => {
    createTestUser(page, 'delete_group_email@email.com', 'delete_group_username');
    createTestGroup(page, 'test_delete_group');

    page.groupAddUser('test_delete_group', 'delete_group_email@email.com');

    // remove the group from user's group list
    page.usersButton.click();
    page.userGroupRemoveButton('delete_group_email@email.com', 'test_delete_group').click();
    page.userRemoveGroupConfirm.click();
    page.userGroupList('delete_group_email@email.com').contains('any_user');
    page.userGroupList('delete_group_email@email.com').contains('delete_group_email@email.com');
    page.userGroupList('delete_group_email@email.com').should('not.contain', 'test_delete_group');

    // check if the group is deleted in Groups
    page.groupsButton.click();
    page.groupUsersList('test_delete_group').should('not.exist');

    page.usersButton.click();
    deleteTestUser(page, 'delete_group_email@email.com');
  });

  it('should check if the new group is deleted after deleting the user', () => {
    createTestUser(page, 'delete_group_delete_user_email@email.com', 'delete_group_delete_user_name');
    createTestGroup(page, 'delete_group_delete_user_group');
    page.groupAddUser('delete_group_delete_user_group', 'delete_group_delete_user_email@email.com');

    // delete user
    page.usersButton.click();
    deleteTestUser(page, 'delete_group_delete_user_email@email.com');

    // check if the group is deleted in Groups
    page.groupsButton.click();
    page.groupUsersList('delete_group_delete_user_group').should('not.exist');
  });

  it('should add group to user and check data in Datasets', () => {
    createTestUser(page, 'add_group_to_user_datasets_email@email.com', 'add_group_to_user_datasets_name');
    page.userAddGroup('add_group_to_user_datasets_email@email.com', 'comp_all');

    // check datasets
    page.userDatasetsCell('add_group_to_user_datasets_email@email.com').should('have.text', 'comp_all');

    page.datasetsButton.click();
    page.datasetUserList('comp_all').contains(
      'add_group_to_user_datasets_name add_group_to_user_datasets_email@email.com'
    );
    page.datasetUserList('comp_all').contains('admin@iossifovlab.com');

    deleteTestUser(page, 'add_group_to_user_datasets_email@email.com');
    page.datasetsButton.click();
    page.datasetUserList('comp_all').contains('admin@iossifovlab.com');
    page.datasetUserList('comp_all').should(
      'not.contain', 'add_group_to_user_datasets_name add_group_to_user_datasets_email@email.com'
    );
  });

  it('should create group, add datasets and check data in Datasets', () => {
    createTestGroup(page, 'add_datasets_group');
    page.groupAddDataset('add_datasets_group', 'iossifov_2014');
    page.groupAddDataset('add_datasets_group', 'comp_all');

    page.datasetsButton.click();
    page.datasetGroupList('iossifov_2014').contains('any_dataset');
    page.datasetGroupList('iossifov_2014').contains('iossifov_2014');
    page.datasetGroupList('iossifov_2014').contains('add_datasets_group');
    page.datasetGroupList('comp_all').contains('any_dataset');
    page.datasetGroupList('comp_all').contains('comp_all');
    page.datasetGroupList('comp_all').contains('add_datasets_group');

    deleteTestGroup(page, 'add_datasets_group');

    page.datasetsButton.click();
    page.datasetGroupList('iossifov_2014').should('not.contain', 'add_datasets_group');
    page.datasetGroupList('comp_all').should('not.contain', 'add_datasets_group');
  });

  it('should create group, add dataset and users and check data in Datasets', () => {
    createTestUser(page, 'test_user_in_datasets1@email.com', 'test_user_in_datasets_username1');
    createTestUser(page, 'test_user_in_datasets2@email.com', 'test_user_in_datasets_username2');
    createTestGroup(page, 'test_user_in_datasets_groupname');

    // add users
    page.groupAddUser('test_user_in_datasets_groupname', 'test_user_in_datasets1@email.com');
    page.groupAddUser('test_user_in_datasets_groupname', 'test_user_in_datasets2@email.com');

    // add dataset
    page.groupAddDataset('test_user_in_datasets_groupname', 'iossifov_2014');

    // check users dataset
    page.usersButton.click();
    page.userDatasetsCell('test_user_in_datasets1@email.com').contains('iossifov_2014');
    page.userDatasetsCell('test_user_in_datasets2@email.com').contains('iossifov_2014');

    // check in Datasets
    page.datasetsButton.click();
    page.datasetUserList('iossifov_2014').contains('admin@iossifovlab.com');
    page.datasetUserList('iossifov_2014').contains('test_user_in_datasets_username1 test_user_in_datasets1@email.com');
    page.datasetUserList('iossifov_2014').contains('test_user_in_datasets_username2 test_user_in_datasets2@email.com');
    page.datasetGroupList('iossifov_2014').contains('any_dataset');
    page.datasetGroupList('iossifov_2014').contains('iossifov_2014');
    page.datasetGroupList('iossifov_2014').contains('test_user_in_datasets_groupname');

    // remove dataset in Groups
    page.groupsButton.click();
    page.groupDatasetsList('test_user_in_datasets_groupname').find('#iossifov_2014-list-item #confirm-button').click();
    page.removeDatasetOrUserConfirmButton.click();

    deleteTestUser(page, 'test_user_in_datasets1@email.com');
    deleteTestUser(page, 'test_user_in_datasets2@email.com');

    // check in Datasets
    page.datasetsButton.click();
    page.datasetUserList('iossifov_2014').contains('admin@iossifovlab.com');
    page.datasetUserList('iossifov_2014').should(
      'not.contain', 'test_user_in_datasets_username1 test_user_in_datasets1@email.com'
    );
    page.datasetUserList('iossifov_2014').should(
      'not.contain', 'test_user_in_datasets_username2 test_user_in_datasets2@email.com'
    );
    page.datasetGroupList('iossifov_2014').contains('any_dataset');
    page.datasetGroupList('iossifov_2014').contains('iossifov_2014');
    page.datasetGroupList('iossifov_2014').should('not.contain', 'test_user_in_datasets_groupname');
  });

  it('should add and remove groups in Datasets', () => {
    createTestUser(page, 'add_remove_group_datasets1@email.com', 'add_remove_group_datasets_username1');
    createTestUser(page, 'add_remove_group_datasets2@email.com', 'add_remove_group_datasets_username2');
    createTestGroup(page, 'add_remove_group_datasets_groupname');

    page.groupAddUser('add_remove_group_datasets_groupname', 'add_remove_group_datasets1@email.com');
    page.groupAddUser('add_remove_group_datasets_groupname', 'add_remove_group_datasets2@email.com');

    page.datasetsButton.click();
    page.datasetAddGroup('comp_denovo', 'add_remove_group_datasets_groupname');

    page.datasetGroupList('comp_denovo').contains('any_dataset');
    page.datasetGroupList('comp_denovo').contains('comp_denovo');
    page.datasetGroupList('comp_denovo').contains('add_remove_group_datasets_groupname');
    page.datasetUserList('comp_denovo').contains(
      'add_remove_group_datasets_username1 add_remove_group_datasets1@email.com'
    );
    page.datasetUserList('comp_denovo').contains(
      'add_remove_group_datasets_username2 add_remove_group_datasets2@email.com'
    );
    page.datasetUserList('comp_denovo').contains('admin@iossifovlab.com');

    page.datasetGroupRemoveButton('comp_denovo', 'add_remove_group_datasets_groupname').click();
    page.datasetsRemoveGroupConfirmButton.click();

    page.datasetGroupList('comp_denovo').should('not.contain', 'add_remove_group_datasets_groupname');
    page.datasetUserList('comp_denovo').should(
      'not.contain', 'add_remove_group_datasets_username1 add_remove_group_datasets1@email.com'
    );
    page.datasetUserList('comp_denovo').should(
      'not.contain', 'add_remove_group_datasets_username2 add_remove_group_datasets2@email.com'
    );

    deleteTestGroup(page, 'add_remove_group_datasets_groupname');
    deleteTestUser(page, 'add_remove_group_datasets1@email.com');
    deleteTestUser(page, 'add_remove_group_datasets2@email.com');
  });
});

function createTestUser(page: UserManagementPage, email: string, name: string): void {
  page.usersButton.click();
  page.createUserButton.click();

  page.emailInputField.type(email);
  page.nameInputField.type(name);
  page.submitUserButton.click();
  page.userCell(email).should('exist');
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
  page.deleteGroupConfirmButton.click();
}
