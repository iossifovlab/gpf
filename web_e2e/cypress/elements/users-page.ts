export class UsersPage {
  get loginDropdownToggleButton() {
    return cy.get('gpf-users').find('#login-dropdown-toggle-button');
  }

  get loginWindow() {
    return cy.get('#login-window');
  }

  get usernameInput() {
    return cy.get('gpf-users').find('#username');
  }

  get passwordInput() {
    return cy.get('gpf-users').find('#password');
  }

  get nextButton() {
    return cy.get('gpf-users').find('#next-button');
  }

  get loginSubmitButton() {
    return cy.get('gpf-users').find('#login-button');
  }

  get logoutButton() {
    return cy.get('gpf-users').find('#logout-button');
  }

  get forgottenPasswordButton() {
    return cy.get('gpf-users').contains('Forgotten password');
  }

  get registerButton() {
    return cy.get('gpf-users').contains('Register');
  }
}
