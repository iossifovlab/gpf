export class UsersPage {
  get loginDropdownToggleButton() {
    return cy.get('gpf-users').get('#login-dropdown-toggle-button');
  }

  get loginWindow() {
    return cy.get('#login-window');
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

  get logoutButton() {
    return cy.get('gpf-users').get('#logout-button');
  }

  get forgottenPasswordButton() {
    return cy.get('gpf-users').contains('Forgotten password');
  }

  get registerButton() {
    return cy.get('gpf-users').contains('Register');
  }
}
