export class UsersPage {
  private get window(): element {
    return cy.get('gpf-users');
  }
  
  public get loginDropdownToggleButton(): element {
    return this.window.find('#login-dropdown-toggle-button');
  }

  public get usernameInput(): element {
    return this.window.find('#username');
  }

  public get passwordInput(): element {
    return this.window.find('#password');
  }

  public get nextButton(): element {
    return this.window.find('#next-button');
  }

  public get loginSubmitButton(): element {
    return this.window.find('#login-button');
  }

  public get logoutButton(): element {
    return this.window.find('#logout-button');
  }

  public get forgottenPasswordButton(): element {
    return this.window.contains('Forgotten password');
  }

  public get registerButton(): element {
    return this.window.contains('Register');
  }
}
