import { UserManagementPage } from "cypress/elements/user-management-page";

describe('User management tests', () => {
  const userManagementPage = new UserManagementPage();

  before(() => {
    userManagementPage.navigateToHome();
    userManagementPage.loginAdmin();
  });

  after(() => {
    userManagementPage.logout();
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('sessionid');
    userManagementPage.navigateToHome();
    userManagementPage.toggleSidenav();
    userManagementPage.sidenavManagementButton.click();
  });

  it('should navigate through all user management tabs', () => {
    userManagementPage.groupsButton.click();
    userManagementPage.groupsTable.should('be.visible');
    
    userManagementPage.datasetsButton.click();
    userManagementPage.datasetsTable.should('be.visible');
  });

  it('should create and delete user', () => {
    userManagementPage.usersTableRows.should('have.length', 3);

    userManagementPage.createUserButton.click();

    userManagementPage.emailInputField.type('test_email@email.com');
    userManagementPage.nameInputField.type('test_name');
    userManagementPage.submitUserButton.click();

    userManagementPage.usersTableRows.should('have.length', 4);
    userManagementPage.usersTableRows.last().should('have.text', ' test_name test_email@email.comany_user test_email@email.com ');

    userManagementPage.userTableDeleteNewestUserButton.click();
    userManagementPage.userTableDeleteUserConfirmButton.click();

    userManagementPage.usersTableRows.should('have.length', 3);
  });

  it('should fail to create user with already used email', () => {
    userManagementPage.usersTableRows.should('have.length', 3);

    createTestUser(userManagementPage, 'test_email@email.com', 'test_name');
    userManagementPage.usersTableRows.should('have.length', 4);

    userManagementPage.createUserButton.click();

    userManagementPage.emailInputField.type('test_email@email.com');
    userManagementPage.nameInputField.type('other_test_name');
    userManagementPage.submitUserButton.click();

    userManagementPage.alertElement.should('have.text', ' Error: wdae user with this email already exists. ');
    userManagementPage.backUserButton.click();
    userManagementPage.backUserConfirmationButton.click();

    userManagementPage.usersTableRows.should('have.length', 4);
    userManagementPage.usersTableRows.last().should('have.text', ' test_name test_email@email.comany_user test_email@email.com ');

    deleteTestUser(userManagementPage);
  });

  it('should search and filter users', () => {
    userManagementPage.usersTableRows.should('have.length', 3);
    userManagementPage.userSearchField.type('admin');
    userManagementPage.usersTableRows.should('have.length', 1);
    userManagementPage.userSearchField.clear();
    // triggers search event
    userManagementPage.userSearchField.type(' ');
    userManagementPage.usersTableRows.should('have.length', 3);
  });

  it('should search and filter a specific user', () => {
    userManagementPage.userSearchField.type('admin');
    cy.wait(500);
    userManagementPage.usersTableRows.last().should('include.text', 'admin');
  });

  it('should search and find user', () => {
    createTestUser(userManagementPage, 'test_email@email.com', 'test_name');
    userManagementPage.userSearchField.type('test_name');
    userManagementPage.usersTableRows.last().should('have.text', ' test_name test_email@email.comany_user test_email@email.com ');

    userManagementPage.userSearchField.clear();
    userManagementPage.userSearchField.type('test_email@email.com');
    userManagementPage.usersTableRows.last().should('have.text', ' test_name test_email@email.comany_user test_email@email.com ');
    cy.reload();

    deleteTestUser(userManagementPage);
  });

  it('should create and delete group', () => {
    userManagementPage.datasetsButton.click();

    userManagementPage.datasetsTableAddGroupToLastDatasetInputField.type('test_group');
    userManagementPage.datasetsTableAddGroupToLastDatasetButton.click();
    cy.wait(500);
    userManagementPage.datasetsTableRows.last().should('include.text', 'test_group');

    userManagementPage.groupsButton.click();
    userManagementPage.groupsTableRows.should('have.length', 9);
    userManagementPage.groupsTableRows.last().should('include.text', 'test_group');

    userManagementPage.datasetsButton.click();
    userManagementPage.datasetsTableRemoveNewestGroupInLastDatasetButton.click();
    userManagementPage.datasetsTableRemoveGroupConfirmButton.click();
    cy.wait(500);
    userManagementPage.datasetsTableRows.last().should('not.include.text', 'test_group');

    userManagementPage.groupsButton.click();
    userManagementPage.groupsTableRows.should('have.length', 8);
    userManagementPage.groupsTableRows.last().should('not.include.text', 'test_group');
  });

  it('should add and remove user from group', () => {
    createTestGroup(userManagementPage, 'test_group');
    createTestUser(userManagementPage, 'test_email@email.com', 'test_name');

    userManagementPage.testUserEditorButton.click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();
    userManagementPage.usersTableRows.last()
      .should('have.text', ' test_name test_email@email.comany_user test_email@email.com test_group × multi ');

    userManagementPage.groupsButton.click();
    userManagementPage.groupsTableRows.last().should('contain.text', 'test_email@email.com');

    userManagementPage.usersButton.click();
    userManagementPage.userTableRemoveUserGroupButton.click();
    userManagementPage.userTableRemoveUserGroupConfirmButton.click();
    cy.reload();
    userManagementPage.usersTableRows.last()
      .should('have.text', ' test_name test_email@email.comany_user test_email@email.com ');

    deleteTestGroup(userManagementPage);
    deleteTestUser(userManagementPage);
  });

  it('should go in user creation and search and find specific group', () => {
    createTestGroup(userManagementPage, 'test_group');

    userManagementPage.usersButton.click();

    userManagementPage.createUserButton.click();

    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownSearch.type('test_group');

    userManagementPage.userWindowGroupDropdownListCheckboxes.should('have.length', 1);
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().should('have.text', 'test_group');

    userManagementPage.backUserButton.click();
    userManagementPage.backUserConfirmationButton.click();

    deleteTestGroup(userManagementPage);
  });

  it('should bulk add and remove users to group', () => {
    createTestGroup(userManagementPage, 'test_group');

    userManagementPage.usersButton.click();
    userManagementPage.userTableEmailElements;

    userManagementPage.userBulkEditButton.click();
    userManagementPage.userBulkEditAddGroupButton.click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.usersEditorAddGroupButton.click();

    userManagementPage.usersTableRows.each(row => {
      userManagementPage.usersTableRows.should('contain.text', 'test_group');
    });

    userManagementPage.groupsButton.click();
    userManagementPage.groupsTableRows.last().then((row) => {
      userManagementPage.usersButton.click();
      userManagementPage.userTableEmailElements.each(el => {
        expect(row.text()).to.contain(el.text());
      });
    });

    userManagementPage.usersButton.click();

    userManagementPage.userBulkEditButton.click();
    userManagementPage.userBulkEditRemoveGroupButton.click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.usersEditorRemoveGroupButton.click();

    userManagementPage.usersTableRows.each(row => {
      userManagementPage.usersTableRows.should('not.contain.text', 'test_group');
    });

    userManagementPage.groupsButton.click();
    userManagementPage.groupsTableRows.last().should('not.contain.text', 'test_group\nmulti');

    deleteTestGroup(userManagementPage);
  });

  it('should give dataset access to user', () => {
    createTestGroup(userManagementPage, 'test_group');
    createTestUser(userManagementPage, 'test_email@email.com', 'test_name');

    userManagementPage.testUserEditorButton.click();

    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowGroupDropdownListCheckboxes.last().click();
    userManagementPage.userWindowGroupDropDownMenuButton.click();
    userManagementPage.userWindowSubmitButton.click();

    userManagementPage.datasetsButton.click();
    userManagementPage.datasetsTableRows.last().should('contain.text', 'test_email@email.com');

    userManagementPage.usersButton.click();
    userManagementPage.userTableRemoveUserGroupButton.click();
    userManagementPage.userTableRemoveUserGroupConfirmButton.click();
    cy.reload();

    userManagementPage.datasetsButton.click();
    userManagementPage.datasetsTableRows.last().should('not.contain.text', 'test_email@email.com');

    deleteTestGroup(userManagementPage);
    deleteTestUser(userManagementPage);
  });
});

function createTestUser(page: UserManagementPage, email: string, name: string) {
  page.usersButton.click();
  page.createUserButton.click();

  page.emailInputField.type(email);
  page.nameInputField.type(name);
  page.submitUserButton.click();
}

function deleteTestUser(page: UserManagementPage) {
  page.usersButton.click();
  page.userTableDeleteNewestUserButton.click();
  page.userTableDeleteUserConfirmButton.click();
  cy.reload();
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
