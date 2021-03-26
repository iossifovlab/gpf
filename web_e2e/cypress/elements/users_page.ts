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

  get logoutButton() {
    return cy.get('gpf-users').get('#logout-button');
  }

  get loginWindow() {
    return cy.get('#login-window');
  }
}
