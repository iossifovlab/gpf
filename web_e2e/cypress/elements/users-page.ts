import 'cypress-if';

export class UsersPage {
  private get window(): element {
    return cy.get('gpf-users');
  }

  public get logInButton(): element {
    return this.window.find('#log-in-button');
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

  public get logOutButton(): element {
    return this.window.find('#log-out-button');
  }

  public get forgottenPasswordButton(): element {
    return this.window.contains('Forgotten password');
  }

  public get registerButton(): element {
    return this.window.contains('Register');
  }

  public waitLoginAfterLogout(): void {
    let done = false;
    let retries = 12;
    while (!(done || retries === 0)) {
      this.window.get('#log-in-button').if('exist').then(() => {
        done = true;
      });
      retries--;
    }
  }
}
