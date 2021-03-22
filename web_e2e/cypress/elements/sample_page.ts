export class AppPage{
  get title() {
    return cy.get('#title');
  }

  login(username: string, password: string) {
    const usersPage = new UsersPage();

    if (!username || !password) {
      return;
    }

    usersPage.loginDropdownToggleButton.click();
    usersPage.usernameInput.type(username);
    usersPage.passwordInput.type(password);
    usersPage.loginSubmitButton.click();
  }
}

export class UsersPage {
  get loginDropdownToggleButton() {
    return cy.get('gpf-users').get('#login-dropdown-toggle-button');
  }

  get usernameInput() {
    return cy.get('gpf-users').get('#username');
  }

  get passwordInput() {
    return cy.get('gpf-users').get('#password');
  }

  get loginSubmitButton() {
    return cy.get('gpf-users').get('#login-button');
  }
}