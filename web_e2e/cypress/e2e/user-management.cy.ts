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
    page.usersTableCells.eq(2).find('>div').should('have.text', 'any_usertest_email@email.com');

    page.usersTableCells.eq(4).find('button[title="Delete user"]').click();
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
    page.usersTableCells.eq(10).should('have.text', 'test_nametest_email@email.com');
    page.usersTableCells.eq(12).find('>div').should('have.text', 'any_usertest_email@email.com');

    deleteTestUser(page, 14);
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
    page.usersTableCells.first().should('have.text', 'test_nametest_email@email.com');
    page.usersTableCells.eq(2).find('>div').should('have.text', 'any_usertest_email@email.com');

    page.userSearchField.clear();
    page.userSearchField.type('test_email@email.com');
    page.usersTableCells.first().should('have.text', 'test_nametest_email@email.com');
    page.usersTableCells.eq(2).find('>div').should('have.text', 'any_usertest_email@email.com');
    deleteTestUser(page, 14);
  });

  // new users tests

  it('should create and delete group', () => {
    page.datasetsButton.click();

    page.datasetsTableAddGroupToLastDatasetInputField.type('test_group');
    page.datasetsTableAddGroupToLastDatasetButton.click();
    page.datasetsTableRows.should('include.text', 'test_group');
    page.datasetsTableRows.last().should('include.text', 'test_group');

    page.groupsButton.click();
    page.groupsTableRows.should('have.length', 12);
    page.groupsTableRows.last().should('include.text', 'test_group');

    page.datasetsButton.click();
    page.datasetsTableRemoveNewestGroupInLastDatasetButton.click();
    page.datasetsTableRemoveGroupConfirmButton.click();
    page.datasetsTableRows.should('not.include.text', 'test_group');

    page.groupsButton.click();
    page.groupsTableRows.should('have.length', 11);
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
    page.usersTableCells.last().should(
      'have.text',
      'test_nametest_email@email.comany_usertest_email@email.comtest_group×multi'
    );

    page.groupsButton.click();
    page.groupsTableRows.last().should('contain.text', 'test_email@email.com');

    page.usersButton.click();
    page.userTableRemoveUserGroupButton.click();
    page.userTableRemoveUserGroupConfirmButton.click();
    waitForRequest('GET', '/gpf/api/v3/users/streaming_search?search=', 'usersUpdate', 200);
    page.usersTableCells.last().should('have.text', 'test_nametest_email@email.comany_usertest_email@email.com');

    deleteTestGroup(page);
    // deleteTestUser(page);
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

    page.cancelUserButton.click();
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
    waitForRequest('GET', '/gpf/api/v3/users/streaming_search?search=**', 'usersUpdate', 200);
    page.datasetsButton.click();
    page.datasetsTableRows.last().should('not.contain.text', 'test_email@email.com');

    deleteTestGroup(page);
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

function deleteTestUser(page: UserManagementPage, index: number): void {
  page.usersButton.click();
  page.usersTableCells.eq(index).find('button[title="Delete user"]').click();
  page.userTableDeleteUserConfirmButton.click();
}

function createTestGroup(page: UserManagementPage, groupName: string): void {
  page.datasetsButton.click();
  page.datasetsTableAddGroupToLastDatasetInputField.type(groupName);
  page.datasetsTableAddGroupToLastDatasetButton.click();
}

function deleteTestGroup(page: UserManagementPage): void {
  page.datasetsButton.click();
  page.datasetsTableRemoveNewestGroupInLastDatasetButton.click();
  page.datasetsTableRemoveGroupConfirmButton.click();
}

function waitForRequest(method: string, url: string, name: string, response: number): void {
  cy.intercept({method: method, url: url}).as(name);
  cy.wait('@' + name).its('response.statusCode').should('eq', response);
}
