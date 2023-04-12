import { UserManagementPage } from 'cypress/elements/user-management-page';
import { UsersPage } from 'cypress/elements/users-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('User management tests for reset password in Users', () => {
  const page = new UserManagementPage();

  before(() => {
    page.cleanup();
    page.navigateToHome(false);
  });

  it('should reset password', () => {
    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    createTestUser(page, 'user_reset_password@email.com', 'test_name');
    page.userHasPasswordCell('user_reset_password@email.com').should('be.empty');
    page.userActionsResetPassword('user_reset_password@email.com').click();
    page.userTableResetPasswordConfirmButton.click();

    cy.request('GET', 'http://mailhog:8025/api/v2/search?kind=to&query=user_reset_password@email.com').then(
      (response) => {
        const lines: string[] = (response.body.items[0].Content.Body as string).split('\r\n');
        const url = lines[1].replace(' http://gpf/gpf/', ''); // remove when commit ??
        cy.visit(url);
        page.newPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.repeatNewPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.newPasswordButton.click();
      }
    );
    page.logout();
    page.login('user_reset_password@email.com', 'XC^ZF*TZXuUChFsv');

    page.logout();
    page.loginAdmin();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    page.userHasPasswordCell('user_reset_password@email.com').find('.fa.fa-check').should('be.visible');
    deleteTestUser(page, 'user_reset_password@email.com');
    page.logout();
  });

  it('should reset password when login', () => {
    const usersPage = new UsersPage();

    page.loginAdmin();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    createTestUser(page, 'forgotten_password@email.com', 'test_name');
    page.logout();

    cy.window().then((win) => {
      cy.stub(win, 'open', (url: string) => {
        win.location.href = `${Cypress.config().baseUrl}accounts/login/?next=/gpf/o/authorize/%3F${url}`;
      }).as('popup');
    });

    usersPage.logInButton.click();

    cy.get('@popup').url().then(url => {
      cy.get('a').first().click();
      cy.get('#id_email').type('forgotten_password@email.com');
      cy.get('input[value="Reset password"]').click();
    });

    cy.request('GET', 'http://mailhog:8025/api/v2/search?kind=to&query=forgotten_password@email.com').then(
      (response) => {
        const lines: string[] = (response.body.items[0].Content.Body as string).split('\r\n');
        const url = lines[1].replace(' http://gpf/gpf/', 'http://172.20.0.6/gpf/'); // remove when commit
        cy.visit(url);
        page.newPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.repeatNewPasswordInput.type('XC^ZF*TZXuUChFsv');
        page.newPasswordButton.click();
      }
    );

    page.login('forgotten_password@email.com', 'XC^ZF*TZXuUChFsv');
    page.logout();

    page.loginAdmin();
    page.navigateToHome();
    page.navigateToSidenavPage(sidenavPageLinks.management);
    deleteTestUser(page, 'forgotten_password@email.com');
    page.logout();
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
    createTestUser(page, 'test_email@email.com', 'test_name');

    page.createUserButton.click();
    page.emailInputField.type('test_email@email.com');
    page.nameInputField.type('test_name');
    page.submitUserButton.click();

    page.alertElement.invoke('text').then((text) => text.trim())
      .should('equal', 'Error: wdae user with this email already exists.');
    page.cancelUserCreationButton.click();

    page.userCell('test_email@email.com').should('exist');
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

    page.cancelUserCreationButton.click();
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

    page.cancelUserCreationButton.click();
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

    page.userSearchField.clear();
    page.userSearchField.type('admin');
    // 5 cells are 1 row
    page.usersTableCells.should('have.length', 5);
    page.userSearchField.clear();
    // triggers search event
    page.userSearchField.type(' ');
    page.usersTableCells.should('have.length', 15);

    deleteTestUser(page, 'test_email@email.com');
  });

  it('should search and not find user', () => {
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

  it('should cancel the process of creating user', () => {
    page.usersButton.click();
    page.createUserButton.click();

    page.nameInputField.type('test_name');
    page.emailInputField.type('test_email@email.com');
    page.cancelUserCreationButton.click();

    page.userCell('test_name').should('not.exist');
  });

  it('should add and remove groups', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.userAddGroupButton('test_email@email.com').should('be.visible');

    // add groups
    page.userAddGroupButton('test_email@email.com').click();
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
    page.userGroupRemoveButton('test_email@email.com', 'comp_all').click();
    page.userRemoveGroupConfirm.click();
    page.userGroupList('test_email@email.com').should('have.text', 'iossifov_2014any_usertest_email@email.com');

    page.userGroupRemoveButton('test_email@email.com', 'iossifov_2014').click();
    page.userCancelRemoveGroupConfirm.click();
    page.userGroupList('test_email@email.com').should('have.text', 'iossifov_2014any_usertest_email@email.com');

    page.userDatasetsCell('test_email@email.com').should('have.text', 'iossifov_2014');

    page.userGroupRemoveButton('test_email@email.com', 'any_user').should('not.exist');
    page.userGroupRemoveButton('test_email@email.com', '#test_email@email.com').should('not.exist');
    deleteTestUser(page, 'test_email@email.com');
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

    page.createGroupNameInput.type('test_group');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    // add user
    page.groupsTableCells.first().should('have.text',
      'test_groupEmpty groups with no users or datasets will be deleted!');
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('research@iossifovlab.com');
    page.findButtonInComponentContainingText('.add-item-button', 'research@iossifovlab.com').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group').should('have.text', 'research@iossifovlab.com');

    // add dataset
    page.groupAddDatasetButton('test_group').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.groupDatasetsList('test_group').should('have.text', 'iossifov_2014');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group').should('exist');

    // delete the group
    page.groupsButton.click();
    page.groupActionsDeleteGroup('test_group').click();
    page.deleteGroupConfirmButton.click();
  });

  it('should create and delete group with user only', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group');

    // add user
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupUsersList('test_group').should('have.text', 'test_email@email.com');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group').should('exist');

    deleteTestGroup(page, 'test_group');
  });

  it('should create and delete group with dataset only', () => {
    createTestGroup(page, 'test_group');

    // add dataset
    page.groupAddDatasetButton('test_group').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.groupsWarningMessage.should('not.exist');
    page.groupDatasetsList('test_group').should('have.text', 'iossifov_2014');

    // check if the group is added
    cy.reload();
    page.groupsButton.click();
    page.groupCell('test_group').should('exist');

    deleteTestGroup(page, 'test_group');
  });

  it('should not create group with no users or datasets', () => {
    page.groupsButton.click();

    page.createGroupButton.click();

    page.createGroupNameInput.type('createGroupNameInput');
    page.createButton.click();
    page.groupsWarningMessage.should('be.visible');
    page.groupsWarningMessage.should('have.text', 'Empty groups with no users or datasets will be deleted!');

    page.datasetsButton.click();
    page.groupsButton.click();
    page.groupCell('test_group').should('not.exist');
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

    page.createGroupNameInput.type('test_group');
    page.cancelGroupCreationButton.click();

    page.groupCell('test_group').should('not.exist');
  });

  it('should fail to create group with already used name', () => {
    createTestUser(page, 'test_email@email.com', 'test_user');
    createTestGroup(page, 'test_group');
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    createTestGroup(page, 'test_group');

    page.alertElement.invoke('text').then((text) => text.trim())
      .should('equal', '\'test_group\' already exists choose another name!');
    page.cancelGroupCreationButton.click();

    deleteTestGroup(page, 'test_group');
    deleteTestUser(page, 'test_email@email.com');
  });

  it('should add and remove users and datasets from group', () => {
    createTestUser(page, 'test_email1@email.com', 'test_name1');
    createTestGroup(page, 'test_group');

    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email1@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email1@email.com').click();

    page.groupAddDatasetButton('test_group').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();

    createTestUser(page, 'test_email2@email.com', 'test_name2');
    createTestUser(page, 'test_email3@email.com', 'test_name3');

    page.groupsButton.click();
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('test_email2@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email2@email.com').click();

    page.groupsMenuSearch.clear();
    page.groupsMenuSearch.type('test_email3@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email3@email.com').click();

    // remove dataset
    page.groupRemoveDatasetButton('test_group', 'iossifov_2014').click();
    page.removeDatasetOrUserConfirmButton.click();

    // remove users
    page.groupRemoveUserButton('test_group', 'test_email1@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();
    page.groupRemoveUserButton('test_group', 'test_email2@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();
    page.groupRemoveUserButton('test_group', 'test_email3@email.com').click();
    page.removeDatasetOrUserConfirmButton.click();

    page.groupsWarningMessage.should('be.visible');

    // check if the group is removed
    cy.reload();
    page.groupCell('test_group').should('not.exist');

    deleteTestUser(page, 'test_email1@email.com');
    deleteTestUser(page, 'test_email2@email.com');
    deleteTestUser(page, 'test_email3@email.com');
  });

  it('should add and remove groups in Users and users in Groups', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group1');
    page.groupAddUserButton('test_group1').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    createTestGroup(page, 'test_group2');
    page.groupAddDatasetButton('test_group2').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();

    // check of the group is in user's group list
    page.usersButton.click();
    page.userGroupList('test_email@email.com').should('have.text', 'any_usertest_email@email.comtest_group1');

    // add group to user's group list
    page.userAddGroupButton('test_email@email.com').click();
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

  it('should check if new groups are added in Groups and the new users ' +
  'are in group any_user when creating user', () => {
    createTestUser(page, 'test_email1@email.com', 'test_name1');
    createTestUser(page, 'test_email2@email.com', 'test_name2');
    createTestUser(page, 'test_email3@email.com', 'test_name3');

    page.groupsButton.click();
    page.groupCell('test_email1@email.com').should('exist');
    page.groupUsersList('test_email1@email.com').should('have.text', 'test_email1@email.com');
    page.groupCell('test_email2@email.com').should('exist');
    page.groupUsersList('test_email2@email.com').should('have.text', 'test_email2@email.com');
    page.groupCell('test_email3@email.com').should('exist');
    page.groupUsersList('test_email3@email.com').should('have.text', 'test_email3@email.com');

    page.groupUsersList('any_user').should('have.text',
      'test_email1@email.comtest_email2@email.comtest_email3@email.com');

    deleteTestUser(page, 'test_email1@email.com');
    deleteTestUser(page, 'test_email2@email.com');
    deleteTestUser(page, 'test_email3@email.com');
  });

  it('should check if the new group is deleted after removing it in Users', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    createTestGroup(page, 'test_group');
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    // remove the group from user's group list
    page.usersButton.click();
    page.userGroupRemoveButton('test_email@email.com', 'test_group').click();
    page.userRemoveGroupConfirm.click();
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
    page.groupAddUserButton('test_group').click();
    page.groupsMenuSearch.type('test_email@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email@email.com').click();

    // delete user
    page.usersButton.click();
    deleteTestUser(page, 'test_email@email.com');

    // check if the group is deleted in Groups
    page.groupsButton.click();
    page.groupUsersList('test_group').should('not.exist');
  });

  it('should add group to user and check data in Datasets', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.userAddGroupButton('test_email@email.com').click();
    page.groupsMenuSearch.type('comp_all');
    page.findButtonInComponentContainingText('.add-item-button', 'comp_all').click();

    // check datasets
    page.userDatasetsCell('test_email@email.com').should('have.text', 'comp_all');

    page.datasetsButton.click();
    // space before admin@iossifovlab.com
    page.datasetUserList('comp_all').should('have.text', ' admin@iossifovlab.comtest_name test_email@email.com');

    deleteTestUser(page, 'test_email@email.com');
    page.datasetsButton.click();
    // space before admin@iossifovlab.com
    page.datasetUserList('comp_all').should('have.text', ' admin@iossifovlab.com');
  });

  it('should create group, add datasets and check data in Datasets', () => {
    createTestGroup(page, 'test_group');
    page.groupAddDatasetButton('test_group').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();
    page.groupsMenuSearch.clear();
    page.groupsMenuSearch.type('comp_all');
    page.findButtonInComponentContainingText('.add-item-button', 'comp_all').click();

    page.datasetsButton.click();
    page.datasetGroupList('iossifov_2014').should('have.text', 'any_datasetiossifov_2014test_group');
    page.datasetGroupList('comp_all').should('have.text', 'any_datasetcomp_alltest_group');

    deleteTestGroup(page, 'test_group');

    page.datasetsButton.click();
    page.datasetUserList('iossifov_2014').should('have.text', ' admin@iossifovlab.com');
    page.datasetUserList('comp_all').should('have.text', ' admin@iossifovlab.com');
  });

  it('should create group, add dataset and users and check data in Datasets', () => {
    createTestUser(page, 'test_email1@email.com', 'test_name1');
    createTestUser(page, 'test_email2@email.com', 'test_name2');
    createTestGroup(page, 'test_group');

    // add users
    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email1@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email1@email.com').click();
    page.groupsMenuSearch.clear();
    page.groupsMenuSearch.type('test_email2@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email2@email.com').click();

    // add dataset
    page.groupDatasetsCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('iossifov_2014');
    page.findButtonInComponentContainingText('.add-item-button', 'iossifov_2014').click();

    // check users dataset
    page.usersButton.click();
    page.userDatasetsCell('test_email1@email.com').should('have.text', 'iossifov_2014');
    page.userDatasetsCell('test_email2@email.com').should('have.text', 'iossifov_2014');

    // check in Datasets
    page.datasetsButton.click();
    page.datasetUserList('iossifov_2014').should('have.text',
      ' admin@iossifovlab.comtest_name1 test_email1@email.comtest_name2 test_email2@email.com');
    page.datasetGroupList('iossifov_2014').should('have.text', 'any_datasetiossifov_2014test_group');

    // remove dataset in Groups
    page.groupsButton.click();
    page.groupDatasetsList('test_group').find('#iossifov_2014-list-item #confirm-button').click();
    page.removeDatasetOrUserConfirmButton.click();

    deleteTestUser(page, 'test_email1@email.com');
    deleteTestUser(page, 'test_email2@email.com');

    // check in Datasets
    page.datasetsButton.click();
    page.datasetUserList('iossifov_2014').should('have.text', ' admin@iossifovlab.com');
    page.datasetGroupList('iossifov_2014').should('have.text', 'any_datasetiossifov_2014');
  });

  it('should add and remove groups in Datasets', () => {
    createTestUser(page, 'test_email1@email.com', 'test_name1');
    createTestUser(page, 'test_email2@email.com', 'test_name2');
    createTestGroup(page, 'test_group');

    page.groupUsersCell('test_group').find('.add-button').click();
    page.groupsMenuSearch.type('test_email1@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email1@email.com').click();
    page.groupsMenuSearch.clear();
    page.groupsMenuSearch.type('test_email2@email.com');
    page.findButtonInComponentContainingText('.add-item-button', 'test_email2@email.com').click();

    page.datasetsButton.click();
    page.datasetAddGroupButton('comp_denovo').click();
    page.groupsMenuSearch.type('test_group');
    page.findButtonInComponentContainingText('.add-item-button', 'test_group').click();

    page.datasetGroupList('comp_denovo').should('have.text', 'any_datasetcomp_denovotest_group');
    page.datasetUserList('comp_denovo').should('have.text',
      ' admin@iossifovlab.comtest_name1 test_email1@email.comtest_name2 test_email2@email.com');

    page.datasetGroupRemoveButton('comp_denovo', 'test_group').click();
    page.datasetsRemoveGroupConfirmButton.click();

    deleteTestGroup(page, 'test_group');
    deleteTestUser(page, 'test_email1@email.com');
    deleteTestUser(page, 'test_email2@email.com');
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
  page.deleteGroupConfirmButton.click();
}
