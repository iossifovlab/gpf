import { Locator, Page } from '@playwright/test';

// Component object for the OAuth login form and the forgotten-password
// flow reachable from it.
export class Login {
  public readonly logInButton: Locator;
  public readonly logInButtonRole: Locator;
  public readonly usernameInput: Locator;
  public readonly passwordInput: Locator;

  public readonly logOutButton: Locator;

  // Forgotten password.
  public readonly forgottenPasswordLink: Locator;
  public readonly forgottenPasswordText: Locator;
  public readonly forgottenPassword: Locator;
  public readonly emailInput: Locator;
  public readonly resetPasswordButton: Locator;

  // Reset-password (set new password) form.
  public readonly newPassword1: Locator;
  public readonly newPassword2: Locator;
  public readonly loginButton: Locator;
  public readonly resetPasswordInput: Locator;
  public readonly resetPasswordText: Locator;

  public constructor(private readonly page: Page) {
    this.logInButton = page.locator('#log-in-button');
    this.logInButtonRole = page.getByRole('button', { name: 'Log In' });
    this.usernameInput = page.locator('input#id_username');
    this.passwordInput = page.locator('input#id_password');
    this.logOutButton = page.locator('#log-out-button');

    this.forgottenPasswordLink = page.getByRole('link', { name: 'forgotten password' });
    this.forgottenPasswordText = page.getByText('forgotten password');
    this.forgottenPassword = page.locator('#forgotten-password');
    this.emailInput = page.locator('input#id_email');
    this.resetPasswordButton = page.getByRole('button', { name: 'Reset password' });

    this.newPassword1 = page.locator('#id_new_password1');
    this.newPassword2 = page.locator('#id_new_password2');
    this.loginButton = page.locator('.login-button');
    this.resetPasswordInput = page.locator('input[value="Reset password"]');
    this.resetPasswordText = page.getByText('Reset password');
  }
}
