import { UserManagementPage } from 'cypress/elements/user-management-page';
import { sidenavPageLinks } from 'cypress/elements/utils';

describe('User management tests', () => {
  const page = new UserManagementPage();

  before(() => {
    page.cleanup();
    page.navigateToHome();
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
    page.usersTableRows.should('have.length', 3);

    page.createUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.type('test_email@email.com');
    page.nameInputField.type('test_name');
    page.submitUserButton.click();

    page.usersTableRows.should('have.length', 4);
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    page.userTableDeleteNewestUserButton.click();
    page.userTableDeleteUserConfirmButton.click();

    page.usersTableRows.should('have.length', 3);
  });

  it('should fail to create user with already used email', () => {
    page.usersTableRows.should('have.length', 3);

    createTestUser(page, 'test_email@email.com', 'test_name');
    page.usersTableRows.should('have.length', 4);

    page.createUserButton.click();
    page.emailInputField.should('be.focused');

    page.emailInputField.type('test_email@email.com');
    page.nameInputField.type('other_test_name');
    page.submitUserButton.click();

    page.alertElement.should('have.text', 'Error: wdae user with this email already exists.');
    page.backUserButton.click();
    page.backUserConfirmationButton.click();

    page.usersTableRows.should('have.length', 4);
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    deleteTestUser(page);
  });

  it('should search and filter users', () => {
    page.usersTableRows.should('have.length', 3);
    page.userSearchField.type('admin');
    page.usersTableRows.should('have.length', 1);
    page.userSearchField.clear();
    // triggers search event
    page.userSearchField.type(' ');
    page.usersTableRows.should('have.length', 3);
  });

  it('should search and filter a specific user', () => {
    page.userSearchField.type('admin');
    page.usersTableRows.should('have.length', 1);
    page.usersTableRows.last().should('include.text', 'admin');
  });

  it('should search and find user', () => {
    createTestUser(page, 'test_email@email.com', 'test_name');
    page.userSearchField.type('test_name');
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    page.userSearchField.clear();
    page.userSearchField.type('test_email@email.com');
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');
    cy.intercept({
      method: 'GET',
      url: '/gpf/api/v3/users/streaming_search?search=**',
    }).as('QueryHandler');
    cy.wait('@QueryHandler').its('response.statusCode').should('equal', 200);
    deleteTestUser(page);
  });

  it('should create and delete group', () => {
    page.datasetsButton.click();

    page.datasetsTableAddGroupToLastDatasetInputField.type('test_group');
    page.datasetsTableAddGroupToLastDatasetButton.click();
    page.datasetsTableRows.should('include.text', 'test_group');
    page.datasetsTableRows.last().should('include.text', 'test_group');

    page.groupsButton.click();
    page.groupsTableRows.should('have.length', 11);
    page.groupsTableRows.last().should('include.text', 'test_group');

    page.datasetsButton.click();
    page.datasetsTableRemoveNewestGroupInLastDatasetButton.click();
    page.datasetsTableRemoveGroupConfirmButton.click();
    page.datasetsTableRows.should('not.include.text', 'test_group');

    page.groupsButton.click();
    page.groupsTableRows.should('have.length', 10);
    page.groupsTableRows.last().should('not.include.text', 'test_group');
  });

  it('should add and remove user from group', () => {
    createTestGroup(page, 'test_group');
    createTestUser(page, 'test_email@email.com', 'test_name');

    page.getUserEditorButtonByEmail('test_email@email.com').click();
    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowGroupDropdownListCheckboxes.last().click();
    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowSubmitButton.click();
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.comtest_group×multi');

    page.groupsButton.click();
    page.groupsTableRows.last().should('contain.text', 'test_email@email.com');

    page.usersButton.click();
    page.userTableRemoveUserGroupButton.click();
    page.userTableRemoveUserGroupConfirmButton.click();
    cy.intercept({
      method: 'GET',
      url: '/gpf/api/v3/users/streaming_search?search=**',
    }).as('QueryHandler');
    cy.wait('@QueryHandler').its('response.statusCode').should('equal', 200);
    page.usersTableRows.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    deleteTestGroup(page);
    deleteTestUser(page);
  });

  it('should go in user creation and search and find specific group', () => {
    createTestGroup(page, 'test_group');

    page.usersButton.click();

    page.createUserButton.click();
    // field focuses automatically and should be awaited to avoid unwanted focus behavior
    page.emailInputField.should('be.focused');

    page.userWindowGroupDropDownMenuButton.click();
    page.userWindowGroupDropdownSearch.type('test_group');

    page.userWindowGroupDropdownListCheckboxes.should('have.length', 1);
    page.userWindowGroupDropdownListCheckboxes.last().should('have.text', 'test_group');

    page.backUserButton.click();
    page.backUserConfirmationButton.click();

    deleteTestGroup(page);
  });

  it('should give dataset access to user', () => {
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
    cy.intercept({
      method: 'GET',
      url: '/gpf/api/v3/users/streaming_search?search=**',
    }).as('QueryHandler');
    cy.wait('@QueryHandler').its('response.statusCode').should('equal', 200);
    page.datasetsButton.click();
    page.datasetsTableRows.last().should('not.contain.text', 'test_email@email.com');

    deleteTestGroup(page);
    deleteTestUser(page);
  });
});

function createTestUser(page: UserManagementPage, email: string, name: string) {
  page.usersButton.click();
  page.createUserButton.click();
  page.emailInputField.should('be.focused');

  page.emailInputField.type(email);
  page.nameInputField.type(name);
  page.submitUserButton.click();
}

function deleteTestUser(page: UserManagementPage) {
  page.usersButton.click();
  page.userTableDeleteNewestUserButton.click();
  page.userTableDeleteUserConfirmButton.click();
}

function createTestGroup(page: UserManagementPage, groupName: string) {
  page.datasetsButton.click();
  page.datasetsTableAddGroupToLastDatasetInputField.type(groupName);
  page.datasetsTableAddGroupToLastDatasetButton.click();
}

function deleteTestGroup(page: UserManagementPage) {
  page.datasetsButton.click();
  page.datasetsTableRemoveNewestGroupInLastDatasetButton.click();
  page.datasetsTableRemoveGroupConfirmButton.click();
}
