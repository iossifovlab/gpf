export class UsersPage {
  public get loginDropdownToggleButton(): element {
    return cy.get('gpf-users').find('#login-dropdown-toggle-button');
  }

  public get loginWindow(): element {
    return cy.get('#login-window');
  }

  public get usernameInput(): element {
    return cy.get('gpf-users').find('#username');
  }

  public get passwordInput(): element {
    return cy.get('gpf-users').find('#password');
  }

  public get nextButton(): element {
    return cy.get('gpf-users').find('#next-button');
  }

  public get loginSubmitButton(): element {
    return cy.get('gpf-users').find('#login-button');
  }

  public get logoutButton(): element {
    return cy.get('gpf-users').find('#logout-button');
  }

  public get forgottenPasswordButton(): element {
    return cy.get('gpf-users').contains('Forgotten password');
  }

  public get registerButton(): element {
    return cy.get('gpf-users').contains('Register');
  }
}
